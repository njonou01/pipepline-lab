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

# Charger toutes les sources
all_data = None
for source in sources:
    source_path = f"s3://{source_bucket}/{source}/"
    try:
        df = spark.read.parquet(source_path)
        print(f"[{source}] Lignes: {df.count()}")
        if all_data is None:
            all_data = df
        else:
            # Union avec colonnes communes
            # Créer un DataFrame avec les colonnes communes, en remplissant celles qui manquent
            df_aligned = df
            common_cols = ["id", "source", "content_clean", "collected_at", "processed_at",
                          "keywords", "categories", "is_remapped", "has_keywords"]
            
            for col_name in common_cols:
                if col_name not in df.columns:
                    # Valeurs par défaut selon le type attendu
                    if col_name in ["keywords", "categories"]:
                        df_aligned = df_aligned.withColumn(col_name, array().cast(ArrayType(StringType())))  # Array vide typé
                    elif col_name in ["is_remapped", "has_keywords"]:
                        df_aligned = df_aligned.withColumn(col_name, lit(False))
                    else:
                        df_aligned = df_aligned.withColumn(col_name, lit(None))
            
            # Sélectionner uniquement les colonnes communes dans le bon ordre
            df_ready = df_aligned.select([col(c) for c in common_cols])
            
            # Union avec le reste des données
            all_data = all_data.union(df_ready)
    except Exception as e:
        print(f"[{source}] Skip: {str(e)}")
        continue

if all_data is None or all_data.count() == 0:
    print("Aucune donnée à agréger")
    job.commit()
    sys.exit(0)

print(f"Total: {all_data.count()} enregistrements")

# =============================================================================
# 1. VOLUME PAR SOURCE ET PAR JOUR
# =============================================================================
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

# =============================================================================
# 2. TRENDING KEYWORDS (top keywords par jour)
# =============================================================================
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

# =============================================================================
# 3. TRENDING CATEGORIES
# =============================================================================
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

# =============================================================================
# 4. ACTIVITE PAR HEURE (pour patterns temporels)
# =============================================================================
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

# =============================================================================
# 5. STATISTIQUES REMAPPING
# =============================================================================
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

# =============================================================================
# 6. RESUME GLOBAL (pour dashboard)
# =============================================================================
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

# Résumé par source
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
