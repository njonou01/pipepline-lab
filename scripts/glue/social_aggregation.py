"""
ETL Job: Social Aggregation (Processed -> Curated)
Crée des agrégations et tendances pour l'analytics.
"""

import sys
import re
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from pyspark.sql.functions import (
    col, sum as _sum, count, avg, max as _max, min as _min,
    current_timestamp, to_date, explode, lower, hour, dayofweek,
    when, lit, collect_list, size, countDistinct, array,
    weekofyear, year, month, concat, lpad, length, lag, round as _round,
    udf, format_string, regexp_replace
)
from pyspark.sql.window import Window
from pyspark.sql.types import ArrayType, StringType, BooleanType

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

# Filtrer les données futures (ne garder que les données avant aujourd'hui)
all_data = all_data.filter(col("collected_at") <= current_timestamp())

print(f"Total: {all_data.count()} enregistrements (après filtrage des dates futures)")

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
    .withColumn("keyword", lower(col("keyword"))) \
    .filter(
        # Pour les mots de ≤2 caractères, vérifier qu'ils sont isolés
        # Approche: ajouter espaces au début/fin du contenu, puis chercher " keyword "
        when(length(col("keyword")) <= 2,
             concat(lit(" "), lower(col("content_clean")), lit(" "))
             .contains(concat(lit(" "), col("keyword"), lit(" ")))
        ).otherwise(lit(True))
    )

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

# =============================================================================
# 7. VOLUME PAR SEMAINE
# =============================================================================
volume_by_week = all_data \
    .withColumn("year", year(col("collected_at"))) \
    .withColumn("week", weekofyear(col("collected_at"))) \
    .withColumn("year_week", concat(col("year"), lit("-W"), lpad(col("week"), 2, "0"))) \
    .groupBy("year_week", "source") \
    .agg(
        count("id").alias("total_posts"),
        countDistinct("id").alias("unique_posts"),
        _min("collected_at").alias("week_start"),
        _max("collected_at").alias("week_end")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("year_week", "source")

print(f"Volume par semaine: {volume_by_week.count()} lignes")

volume_by_week \
    .write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(f"{analytics_path}volume_by_week/")

# =============================================================================
# 8. VOLUME PAR MOIS
# =============================================================================
volume_by_month = all_data \
    .withColumn("year", year(col("collected_at"))) \
    .withColumn("month", month(col("collected_at"))) \
    .withColumn("year_month", concat(col("year"), lit("-"), lpad(col("month"), 2, "0"))) \
    .groupBy("year_month", "source") \
    .agg(
        count("id").alias("total_posts"),
        countDistinct("id").alias("unique_posts"),
        _min("collected_at").alias("month_start"),
        _max("collected_at").alias("month_end")
    ) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("year_month", "source")

print(f"Volume par mois: {volume_by_month.count()} lignes")

volume_by_month \
    .write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(f"{analytics_path}volume_by_month/")

# =============================================================================
# 9. TAUX DE CROISSANCE JOUR/JOUR
# =============================================================================
window_growth = Window.partitionBy("source").orderBy("date")

growth_rate = all_data \
    .withColumn("date", to_date(col("collected_at"))) \
    .groupBy("date", "source") \
    .agg(count("id").alias("total_posts")) \
    .withColumn("prev_day_posts", lag("total_posts", 1).over(window_growth)) \
    .withColumn("growth_pct",
        when(col("prev_day_posts").isNotNull() & (col("prev_day_posts") > 0),
             _round((col("total_posts") - col("prev_day_posts")) / col("prev_day_posts") * 100, 2)
        ).otherwise(lit(None))
    ) \
    .withColumn("growth_abs", col("total_posts") - col("prev_day_posts")) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("source", "date")

print(f"Taux de croissance: {growth_rate.count()} lignes")

growth_rate \
    .write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(f"{analytics_path}growth_rate/")

# =============================================================================
# 10. STATS CONTENU (longueur, etc.)
# =============================================================================
content_stats = all_data \
    .withColumn("date", to_date(col("collected_at"))) \
    .withColumn("content_length", length(col("content_clean"))) \
    .groupBy("date", "source") \
    .agg(
        count("id").alias("total_posts"),
        _round(avg("content_length"), 0).alias("avg_length"),
        _min("content_length").alias("min_length"),
        _max("content_length").alias("max_length"),
        _sum(when(col("content_length") > 280, 1).otherwise(0)).alias("long_posts"),
        _sum(when(col("content_length") <= 280, 1).otherwise(0)).alias("short_posts")
    ) \
    .withColumn("long_posts_pct", _round(col("long_posts") / col("total_posts") * 100, 2)) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("date", "source")

print(f"Stats contenu: {content_stats.count()} lignes")

content_stats \
    .write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(f"{analytics_path}content_stats/")

# =============================================================================
# 11. KEYWORDS CROSS-SOURCE (presents sur plusieurs sources)
# =============================================================================
cross_source_keywords = keywords_exploded \
    .groupBy("keyword") \
    .agg(
        count("*").alias("total_mentions"),
        countDistinct("source").alias("sources_count"),
        collect_list("source").alias("sources_list")
    ) \
    .filter(col("sources_count") >= 2) \
    .withColumn("is_viral", when(col("sources_count") >= 3, True).otherwise(False)) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy(col("sources_count").desc(), col("total_mentions").desc())

print(f"Keywords cross-source: {cross_source_keywords.count()} lignes")

cross_source_keywords \
    .write \
    .mode("overwrite") \
    .parquet(f"{trends_path}cross_source_keywords/")

# =============================================================================
# 12. KEYWORDS PAR SOURCE (top keywords de chaque source)
# =============================================================================
keywords_by_source = keywords_exploded \
    .groupBy("source", "keyword") \
    .agg(count("*").alias("mentions")) \
    .withColumn("aggregated_at", current_timestamp()) \
    .orderBy("source", col("mentions").desc())

print(f"Keywords par source: {keywords_by_source.count()} lignes")

keywords_by_source \
    .write \
    .mode("overwrite") \
    .partitionBy("source") \
    .parquet(f"{trends_path}keywords_by_source/")

# =============================================================================
# 13. RESUME ETENDU
# =============================================================================
# Calculer unique_keywords separement (explode ne peut pas etre dans agg)
unique_kw_count = keywords_exploded.select("keyword").distinct().count()

extended_summary = all_data \
    .withColumn("content_length", length(col("content_clean"))) \
    .agg(
        count("id").alias("total_posts"),
        countDistinct("source").alias("active_sources"),
        countDistinct(to_date(col("collected_at"))).alias("days_covered"),
        _min("collected_at").alias("first_post"),
        _max("collected_at").alias("last_post"),
        _round(avg("content_length"), 0).alias("avg_content_length"),
        _sum(when(col("is_remapped"), 1).otherwise(0)).alias("total_remapped"),
        _sum(when(col("has_keywords"), 1).otherwise(0)).alias("total_with_keywords")
    ) \
    .withColumn("unique_keywords", lit(unique_kw_count)) \
    .withColumn("aggregated_at", current_timestamp())

extended_summary \
    .write \
    .mode("overwrite") \
    .parquet(f"{reports_path}extended_summary/")

print("Agregations terminees")

job.commit()
