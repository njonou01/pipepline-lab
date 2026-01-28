"""
ETL Job: Social Data Transform (Raw -> Processed)
Transforme les données sociales brutes (Bluesky, Nostr, HackerNews, StackOverflow, RSS)
en données nettoyées au format Parquet.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, current_timestamp, when, lit, to_timestamp, explode,
    from_json, size, lower, regexp_replace, trim, coalesce, array
)
from pyspark.sql.types import (
    StructType, StructField, StringType, ArrayType,
    TimestampType, BooleanType, IntegerType
)

args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'source_bucket',
    'target_bucket',
    'source_name'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

source_name = args['source_name']
source_path = f"s3://{args['source_bucket']}/{source_name}/"
target_path = f"s3://{args['target_bucket']}/{source_name}/"

print(f"Source: {source_path}")
print(f"Target: {target_path}")
print(f"Processing: {source_name}")

can_process = False
raw_df = None

try:
    print(f"Tentative de lecture depuis: {source_path}")
    
    # Lecture avec support des Job Bookmarks via DynamicFrame
    dynamic_frame = glueContext.create_dynamic_frame.from_options(
        format_options={"multiline": False},
        connection_type="s3",
        format="json",
        connection_options={
            "paths": [source_path],
            "recurse": True
        },
        transformation_ctx=f"extract_{source_name}"
    )
    
    raw_df = dynamic_frame.toDF()
    
    row_count = raw_df.count()
    print(f"Lignes lues: {row_count}")
    
    if row_count == 0:
        print(f"WARN: Aucune donnee a traiter pour {source_name}")
        print(f"Vérifiez:")
        print(f"  1. Les fichiers existent dans {source_path}")
        print(f"  2. Les fichiers JSON sont au bon format (1 JSON par ligne)")
        print(f"  3. Les fichiers ne sont pas vides")
        can_process = False
    else:
        raw_df.printSchema()
        can_process = True

except Exception as e:
    print(f"ERROR: Erreur de lecture pour {source_name}: {str(e)}")
    import traceback
    traceback.print_exc()
    can_process = False

if can_process:
    available_cols = raw_df.columns
    content_col = None
    
    if "content" in available_cols:
        content_col = col("content")
    elif "summary" in available_cols:
        content_col = col("summary")
    elif "text" in available_cols:     # HackerNews
        content_col = col("text")
    elif "body" in available_cols:     # StackOverflow
        content_col = col("body")
    elif "title" in available_cols:
        content_col = col("title")
    else:
        content_col = lit("")
    
    time_col = None
    if "collected_at" in available_cols:
        time_col = to_timestamp(col("collected_at"))
    elif "published" in available_cols:
        time_col = to_timestamp(col("published"))
    elif "created_at" in available_cols:    # Nostr / Bluesky
        time_col = to_timestamp(col("created_at"))
    elif "timestamp" in available_cols:     # HackerNews / StackOverflow (integer timestamp)
        time_col = to_timestamp(col("timestamp"))
    else:
        time_col = current_timestamp()
    
    transformed_df = raw_df \
        .withColumn("id", col("id").cast(StringType())) \
        .withColumn("source", lit(source_name)) \
        .withColumn("content_clean",
            trim(regexp_replace(coalesce(content_col, lit("")), r'[\n\r\t]+', ' '))
        ) \
        .withColumn("collected_at", time_col) \
        .withColumn("processed_at", current_timestamp())
    
    def safe_col(col_name, default_val=lit(None)):
        if col_name in available_cols:
            return col(col_name)
        return default_val
    
    if source_name == "bluesky":
        transformed_df = transformed_df \
            .withColumn("author", safe_col("author", lit(""))) \
            .withColumn("created_at", to_timestamp(safe_col("created_at"))) \
            .withColumn("likes", coalesce(safe_col("likes"), lit(0)).cast(IntegerType())) \
            .withColumn("reposts", coalesce(safe_col("reposts"), lit(0)).cast(IntegerType()))
    
    elif source_name == "nostr":
        transformed_df = transformed_df \
            .withColumn("pubkey", safe_col("pubkey", lit(""))) \
            .withColumn("created_at", to_timestamp(safe_col("created_at"))) \
            .withColumn("kind", coalesce(safe_col("kind"), lit(1)).cast(IntegerType()))
    
    elif source_name == "hackernews":
        transformed_df = transformed_df \
            .withColumn("author", safe_col("author", lit(""))) \
            .withColumn("title", safe_col("title", lit(""))) \
            .withColumn("url", safe_col("url", lit(""))) \
            .withColumn("score", coalesce(safe_col("score"), lit(0)).cast(IntegerType())) \
            .withColumn("comments", coalesce(safe_col("comments"), lit(0)).cast(IntegerType())) \
            .withColumn("type", safe_col("type", lit("story")))
    
    elif source_name == "stackoverflow":
        transformed_df = transformed_df \
            .withColumn("title", safe_col("title", lit(""))) \
            .withColumn("link", safe_col("link", lit(""))) \
            .withColumn("score", coalesce(safe_col("score"), lit(0)).cast(IntegerType())) \
            .withColumn("answer_count", coalesce(safe_col("answer_count"), lit(0)).cast(IntegerType())) \
            .withColumn("view_count", coalesce(safe_col("view_count"), lit(0)).cast(IntegerType())) \
            .withColumn("is_answered", coalesce(safe_col("is_answered"), lit(False)).cast(BooleanType()))
    
    elif source_name == "rss":
        transformed_df = transformed_df \
            .withColumn("title", safe_col("title", lit(""))) \
            .withColumn("link", safe_col("link", lit(""))) \
            .withColumn("feed_source", safe_col("feed_source", lit(""))) \
            .withColumn("published_at", to_timestamp(safe_col("published_at")))
    
    
    from pyspark.sql.functions import flatten, expr

    if source_name == "nostr":
        if "tags" in available_cols:
            keywords_col = expr("transform(tags, x -> x[0])")
        elif "keywords" in available_cols:
            keywords_col = col("keywords")
        else:
            keywords_col = array().cast(ArrayType(StringType()))
    else:
        if "mapped_keywords" in available_cols:
            keywords_col = col("mapped_keywords")
        elif "keywords" in available_cols:
            keywords_col = col("keywords")
        else:
            keywords_col = array().cast(ArrayType(StringType()))

    if "categories" in available_cols:
        categories_col = col("categories")
    else:
        categories_col = array().cast(ArrayType(StringType()))
    
    transformed_df = transformed_df \
        .withColumn("keywords", keywords_col) \
        .withColumn("categories", categories_col) \
        .withColumn("is_remapped", coalesce(safe_col("is_remapped"), lit(False)).cast(BooleanType())) \
        .withColumn("has_keywords", when(size(col("keywords")) > 0, True).otherwise(False))
    
    transformed_df = transformed_df.dropDuplicates(["id"])
    
    transformed_df = transformed_df.filter(
        (col("id").isNotNull()) &
        (col("content_clean") != "")
    )
    
    print(f"Lignes après transformation: {transformed_df.count()}")
    
    transformed_df \
        .write \
        .mode("append") \
        .partitionBy("source") \
        .parquet(target_path)
    
    print(f"OK: Transformation {source_name} terminee avec succes")
else:
    print(f"SKIP: Pas de donnees a traiter pour {source_name} - Job termine")

job.commit()
