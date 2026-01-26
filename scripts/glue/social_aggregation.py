"""
ETL Job: Social Aggregation (Processed -> Curated)
Crée des agrégations et tendances pour l'analytics.
"""

import sys
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, sum as _sum, count, avg, max as _max, min as _min,
    current_timestamp, to_date, explode, lower, hour, dayofweek,
    when, lit, collect_list, size, countDistinct, array
)

args = getResolvedOptions(sys.argv, [
    'JOB_NAME',
    'source_bucket',
    'target_bucket'
])

sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

sources = ["bluesky", "nostr", "hackernews", "stackoverflow", "rss"]
source_bucket = args['source_bucket']
target_bucket = args['target_bucket']

analytics_path = f"s3://{target_bucket}/analytics/"
reports_path = f"s3://{target_bucket}/reports/"
trends_path = f"s3://{target_bucket}/trends/"

print(f"Source bucket: {source_bucket}")
print(f"Target analytics: {analytics_path}")

from pyspark.sql.types import ArrayType, StringType

common_cols = ["id", "source", "content_clean", "collected_at", "processed_at",
              "keywords", "categories", "is_remapped", "has_keywords"]

all_data = None
for source in sources:
    source_path = f"s3://{source_bucket}/{source}/"
    try:
        df = spark.read.parquet(source_path)
        row_count = df.count()
        print(f"[{source}] Lignes: {row_count}")

        if row_count == 0:
            print(f"[{source}] Skip: pas de donnees")
            continue

        for col_name in common_cols:
            if col_name not in df.columns:
                if col_name in ["keywords", "categories"]:
                    df = df.withColumn(col_name, array().cast(ArrayType(StringType())))
                elif col_name in ["is_remapped", "has_keywords"]:
                    df = df.withColumn(col_name, lit(False))
                else:
                    df = df.withColumn(col_name, lit(None))

        df_ready = df.select([col(c) for c in common_cols])

        if all_data is None:
            all_data = df_ready
        else:
            all_data = all_data.union(df_ready)

        print(f"[{source}] OK - Total cumule: {all_data.count()}")

    except Exception as e:
        print(f"[{source}] Skip: {str(e)}")
        continue

if all_data is None or all_data.count() == 0:
    print("Aucune donnée à agréger")
    job.commit()
    sys.exit(0)

print(f"Total: {all_data.count()} enregistrements")

volume_by_source = all_data \
    .withColumn("date", to_date(col("collected_at"))) \
    .groupBy("date", "source") \
    .agg(
        count("id").alias("total_posts"),
        countDistinct("id").alias("unique_posts")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("date", "source")

print(f"Volume par source: {volume_by_source.count()} lignes")

volume_by_source \
    .write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(f"{analytics_path}volume_by_source/")

keywords_exploded = all_data \
    .withColumn("date", to_date(col("collected_at"))) \
    .withColumn("keyword", explode(col("keywords"))) \
    .withColumn("keyword", lower(col("keyword")))

trending_keywords = keywords_exploded \
    .groupBy("date", "keyword") \
    .agg(
        count("*").alias("mentions"),
        countDistinct("source").alias("sources_count")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy(col("date").desc(), col("mentions").desc())

print(f"Trending keywords: {trending_keywords.count()} lignes")

trending_keywords \
    .write \
    .mode("overwrite") \
    .parquet(f"{trends_path}keywords/")

categories_exploded = all_data \
    .withColumn("date", to_date(col("collected_at"))) \
    .withColumn("category", explode(col("categories")))

trending_categories = categories_exploded \
    .groupBy("date", "category") \
    .agg(
        count("*").alias("mentions"),
        countDistinct("source").alias("sources_count")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy(col("date").desc(), col("mentions").desc())

print(f"Trending categories: {trending_categories.count()} lignes")

trending_categories \
    .write \
    .mode("overwrite") \
    .parquet(f"{trends_path}categories/")

hourly_activity = all_data \
    .withColumn("hour", hour(col("collected_at"))) \
    .withColumn("day_of_week", dayofweek(col("collected_at"))) \
    .groupBy("source", "hour", "day_of_week") \
    .agg(count("id").alias("post_count")) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("source", "day_of_week", "hour")

print(f"Activité horaire: {hourly_activity.count()} lignes")

hourly_activity \
    .write \
    .mode("overwrite") \
    .parquet(f"{analytics_path}hourly_activity/")

remapping_stats = all_data \
    .withColumn("date", to_date(col("collected_at"))) \
    .groupBy("date", "source") \
    .agg(
        count("*").alias("total"),
        _sum(when(col("is_remapped"), 1).otherwise(0)).alias("remapped_count"),
        _sum(when(col("has_keywords"), 1).otherwise(0)).alias("with_keywords_count")
    ) \
    .withColumn("remapped_pct", col("remapped_count") / col("total") * 100) \
    .withColumn("keywords_pct", col("with_keywords_count") / col("total") * 100) \
    .withColumn("aggregated_at", current_timestamp())

print(f"Stats remapping: {remapping_stats.count()} lignes")

remapping_stats \
    .write \
    .mode("overwrite") \
    .parquet(f"{analytics_path}remapping_stats/")

global_summary = all_data.agg(
    count("id").alias("total_posts"),
    countDistinct("source").alias("active_sources"),
    _min("collected_at").alias("first_post"),
    _max("collected_at").alias("last_post"),
    _sum(when(col("is_remapped"), 1).otherwise(0)).alias("total_remapped"),
    _sum(when(col("has_keywords"), 1).otherwise(0)).alias("total_with_keywords")
).withColumn("aggregated_at", current_timestamp())

global_summary \
    .write \
    .mode("overwrite") \
    .parquet(f"{reports_path}global_summary/")

source_summary = all_data \
    .groupBy("source") \
    .agg(
        count("id").alias("total_posts"),
        _min("collected_at").alias("first_post"),
        _max("collected_at").alias("last_post")
    ) \
    .withColumn("aggregated_at", current_timestamp())

source_summary \
    .write \
    .mode("overwrite") \
    .parquet(f"{reports_path}source_summary/")

print("Agrégations terminées")

job.commit()
