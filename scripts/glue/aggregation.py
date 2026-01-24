"""
ETL Job: Aggregation (Processed -> Curated)
Ce script Glue crée des agrégations pour l'analytics.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, sum as _sum, count, avg, max as _max, min as _min,
    current_timestamp, date_trunc, to_date
)

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
orders_path = f"s3://{args['source_bucket']}/orders/"
analytics_path = f"s3://{args['target_bucket']}/analytics/"
reports_path = f"s3://{args['target_bucket']}/reports/"

print(f"Source orders: {orders_path}")
print(f"Target analytics: {analytics_path}")

# Lecture des commandes transformées
try:
    orders_df = spark.read.parquet(orders_path)

    if orders_df.count() == 0:
        print("Aucune donnée à agréger")
        job.commit()
        sys.exit(0)

    print(f"Nombre de commandes: {orders_df.count()}")

except Exception as e:
    print(f"Erreur de lecture: {str(e)}")
    job.commit()
    sys.exit(0)

# =============================================================================
# AGGREGATION 1: Ventes par jour
# =============================================================================
daily_sales = orders_df \
    .withColumn("order_day", to_date(col("order_date"))) \
    .groupBy("order_day") \
    .agg(
        count("order_id").alias("total_orders"),
        _sum("total_amount").alias("total_revenue"),
        avg("total_amount").alias("avg_order_value"),
        _sum("quantity").alias("total_items_sold")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("order_day")

print(f"Jours agrégés: {daily_sales.count()}")

daily_sales \
    .write \
    .mode("overwrite") \
    .parquet(f"{analytics_path}daily_sales/")

# =============================================================================
# AGGREGATION 2: Ventes par produit
# =============================================================================
product_sales = orders_df \
    .groupBy("product_id") \
    .agg(
        count("order_id").alias("total_orders"),
        _sum("quantity").alias("total_quantity_sold"),
        _sum("total_amount").alias("total_revenue"),
        avg("price").alias("avg_price")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy(col("total_revenue").desc())

print(f"Produits agrégés: {product_sales.count()}")

product_sales \
    .write \
    .mode("overwrite") \
    .parquet(f"{analytics_path}product_sales/")

# =============================================================================
# AGGREGATION 3: Ventes par client
# =============================================================================
customer_sales = orders_df \
    .groupBy("customer_id") \
    .agg(
        count("order_id").alias("total_orders"),
        _sum("total_amount").alias("total_spent"),
        avg("total_amount").alias("avg_order_value"),
        _min("order_date").alias("first_order"),
        _max("order_date").alias("last_order")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy(col("total_spent").desc())

print(f"Clients agrégés: {customer_sales.count()}")

customer_sales \
    .write \
    .mode("overwrite") \
    .parquet(f"{analytics_path}customer_sales/")

# =============================================================================
# AGGREGATION 4: Résumé global (pour dashboard)
# =============================================================================
global_summary = orders_df.agg(
    count("order_id").alias("total_orders"),
    _sum("total_amount").alias("total_revenue"),
    avg("total_amount").alias("avg_order_value"),
    _sum("quantity").alias("total_items_sold"),
    _min("order_date").alias("first_order_date"),
    _max("order_date").alias("last_order_date")
).withColumn("aggregated_at", current_timestamp())

global_summary \
    .write \
    .mode("overwrite") \
    .parquet(f"{reports_path}global_summary/")

print("Agrégations terminées avec succès")

job.commit()
