
resource "aws_glue_catalog_database" "main" {
  name        = "${replace(local.name_prefix, "-", "_")}_db"
  description = "UCCNCT Data Lake database"
}

# Tables RAW pour chaque source
resource "aws_glue_catalog_table" "raw_social" {
  for_each      = toset(["bluesky", "nostr", "hackernews", "stackoverflow", "rss"])
  name          = "raw_${each.value}"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "json"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw.id}/${each.value}/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "id"
      type = "string"
    }
    columns {
      name = "content"
      type = "string"
    }
    columns {
      name = "old_content"
      type = "string"
    }
    columns {
      name = "author"
      type = "string"
    }
    columns {
      name = "collected_at"
      type = "timestamp"
    }
    columns {
      name = "keywords"
      type = "array<string>"
    }
    columns {
      name = "categories"
      type = "array<string>"
    }
    columns {
      name = "is_remapped"
      type = "boolean"
    }
  }
}

# Tables PROCESSED (Parquet)
resource "aws_glue_catalog_table" "processed_social" {
  for_each      = toset(["bluesky", "nostr", "hackernews", "stackoverflow", "rss"])
  name          = "processed_${each.value}"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.processed.id}/${each.value}/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "id"
      type = "string"
    }
    columns {
      name = "source"
      type = "string"
    }
    columns {
      name = "content_clean"
      type = "string"
    }
    columns {
      name = "collected_at"
      type = "timestamp"
    }
    columns {
      name = "processed_at"
      type = "timestamp"
    }
    columns {
      name = "keywords"
      type = "array<string>"
    }
    columns {
      name = "categories"
      type = "array<string>"
    }
    columns {
      name = "is_remapped"
      type = "boolean"
    }
    columns {
      name = "has_keywords"
      type = "boolean"
    }
  }
}

# Tables CURATED - Analytics
resource "aws_glue_catalog_table" "curated_trending_keywords" {
  name          = "trending_keywords"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.curated.id}/trends/keywords/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "date"
      type = "date"
    }
    columns {
      name = "keyword"
      type = "string"
    }
    columns {
      name = "mentions"
      type = "bigint"
    }
    columns {
      name = "sources_count"
      type = "bigint"
    }
    columns {
      name = "aggregated_at"
      type = "timestamp"
    }
  }
}

resource "aws_glue_catalog_table" "curated_trending_categories" {
  name          = "trending_categories"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.curated.id}/trends/categories/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "date"
      type = "date"
    }
    columns {
      name = "category"
      type = "string"
    }
    columns {
      name = "mentions"
      type = "bigint"
    }
    columns {
      name = "sources_count"
      type = "bigint"
    }
    columns {
      name = "aggregated_at"
      type = "timestamp"
    }
  }
}

resource "aws_glue_catalog_table" "curated_volume_by_source" {
  name          = "volume_by_source"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.curated.id}/analytics/volume_by_source/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "date"
      type = "date"
    }
    columns {
      name = "source"
      type = "string"
    }
    columns {
      name = "total_posts"
      type = "bigint"
    }
    columns {
      name = "unique_posts"
      type = "bigint"
    }
    columns {
      name = "aggregated_at"
      type = "timestamp"
    }
  }
}

# Crawler pour découvrir les schémas
resource "aws_glue_crawler" "processed" {
  name          = "${local.name_prefix}-processed-crawler"
  database_name = aws_glue_catalog_database.main.name
  role          = local.lab_role_arn

  s3_target {
    path = "s3://${aws_s3_bucket.processed.id}/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name = "${local.name_prefix}-processed-crawler"
  }
}

resource "aws_glue_crawler" "curated" {
  name          = "${local.name_prefix}-curated-crawler"
  database_name = aws_glue_catalog_database.main.name
  role          = local.lab_role_arn

  s3_target {
    path = "s3://${aws_s3_bucket.curated.id}/"
  }

  schema_change_policy {
    delete_behavior = "LOG"
    update_behavior = "UPDATE_IN_DATABASE"
  }

  tags = {
    Name = "${local.name_prefix}-curated-crawler"
  }
}

# Job Transform (Raw -> Processed)
resource "aws_glue_job" "transform_social" {
  for_each = toset(["bluesky", "nostr", "hackernews", "stackoverflow", "rss"])
  name     = "${local.name_prefix}-transform-${each.value}"
  role_arn = local.lab_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/glue/social_transform.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"   = "python"
    "--TempDir"        = "s3://${aws_s3_bucket.scripts.id}/temp/"
    "--source_bucket"  = aws_s3_bucket.raw.id
    "--target_bucket"  = aws_s3_bucket.processed.id
    "--source_name"    = each.value
    "--enable-metrics" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 30

  tags = {
    Name   = "${local.name_prefix}-transform-${each.value}"
    Source = each.value
  }

  depends_on = [aws_s3_object.glue_script_transform]
}

# Job Aggregation (Processed -> Curated)
resource "aws_glue_job" "aggregation" {
  name     = "${local.name_prefix}-aggregation"
  role_arn = local.lab_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/glue/social_aggregation.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"   = "python"
    "--TempDir"        = "s3://${aws_s3_bucket.scripts.id}/temp/"
    "--source_bucket"  = aws_s3_bucket.processed.id
    "--target_bucket"  = aws_s3_bucket.curated.id
    "--enable-metrics" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 60

  tags = {
    Name = "${local.name_prefix}-aggregation"
  }

  depends_on = [aws_s3_object.glue_script_aggregation]
}
