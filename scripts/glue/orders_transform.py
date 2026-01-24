"""
ETL Job: Orders Transform (Raw -> Processed)
Ce script Glue transforme les commandes brutes en données nettoyées au format Parquet.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.dynamicframe import DynamicFrame
from pyspark.sql.functions import col, current_timestamp, when, lit, to_timestamp
from pyspark.sql.types import DoubleType, IntegerType

# Récupération des arguments
args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'source_bucket',
    'target_bucket'
])

# Initialisation du contexte Glue
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Chemins S3
source_path = f"s3://{args['source_bucket']}/orders/"
target_path = f"s3://{args['target_bucket']}/orders/"

print(f"Source: {source_path}")
print(f"Target: {target_path}")

# Lecture des données brutes
try:
    raw_df = spark.read.json(source_path)

    if raw_df.count() == 0:
        print("Aucune donnée à traiter")
        job.commit()
        sys.exit(0)

    print(f"Nombre de lignes lues: {raw_df.count()}")
    raw_df.printSchema()

except Exception as e:
    print(f"Erreur de lecture: {str(e)}")
    job.commit()
    sys.exit(0)

# Transformations
transformed_df = raw_df \
    .withColumn("quantity", col("quantity").cast(IntegerType())) \
    .withColumn("price", col("price").cast(DoubleType())) \
    .withColumn("total_amount", col("quantity") * col("price")) \
    .withColumn("order_date", to_timestamp(col("order_date"))) \
    .withColumn("processed_at", current_timestamp()) \
    .withColumn("status",
        when(col("status").isNull(), lit("pending"))
        .otherwise(col("status"))
    )

# Suppression des doublons
transformed_df = transformed_df.dropDuplicates(["order_id"])

# Filtrage des données invalides
transformed_df = transformed_df.filter(
    (col("order_id").isNotNull()) &
    (col("customer_id").isNotNull()) &
    (col("quantity") > 0) &
    (col("price") > 0)
)

print(f"Nombre de lignes après transformation: {transformed_df.count()}")

# Écriture en Parquet partitionné par date
transformed_df \
    .write \
    .mode("overwrite") \
    .partitionBy("status") \
    .parquet(target_path)

print("Transformation terminée avec succès")

job.commit()
