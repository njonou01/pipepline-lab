
resource "aws_glue_catalog_database" "main" {
  name        = "${replace(local.name_prefix, "-", "_")}_db"
  description = "Data Lake database"
}

resource "aws_glue_catalog_table" "raw_orders" {
  name          = "raw_orders"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "json"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.raw.id}/orders/"
    input_format  = "org.apache.hadoop.mapred.TextInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat"

    ser_de_info {
      serialization_library = "org.openx.data.jsonserde.JsonSerDe"
    }

    columns {
      name = "order_id"
      type = "string"
    }
    columns {
      name = "customer_id"
      type = "string"
    }
    columns {
      name = "product_id"
      type = "string"
    }
    columns {
      name = "quantity"
      type = "int"
    }
    columns {
      name = "price"
      type = "double"
    }
    columns {
      name = "order_date"
      type = "timestamp"
    }
    columns {
      name = "status"
      type = "string"
    }
  }
}

resource "aws_glue_catalog_table" "processed_orders" {
  name          = "processed_orders"
  database_name = aws_glue_catalog_database.main.name
  table_type    = "EXTERNAL_TABLE"

  parameters = {
    classification = "parquet"
  }

  storage_descriptor {
    location      = "s3://${aws_s3_bucket.processed.id}/orders/"
    input_format  = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat"
    output_format = "org.apache.hadoop.hive.ql.io.parquet.MapredParquetOutputFormat"

    ser_de_info {
      serialization_library = "org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe"
    }

    columns {
      name = "order_id"
      type = "string"
    }
    columns {
      name = "customer_id"
      type = "string"
    }
    columns {
      name = "product_id"
      type = "string"
    }
    columns {
      name = "quantity"
      type = "int"
    }
    columns {
      name = "price"
      type = "double"
    }
    columns {
      name = "total_amount"
      type = "double"
    }
    columns {
      name = "order_date"
      type = "timestamp"
    }
    columns {
      name = "status"
      type = "string"
    }
  }
}

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

resource "aws_glue_job" "transform_orders" {
  name     = "${local.name_prefix}-transform-orders"
  role_arn = local.lab_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/glue/orders_transform.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"   = "python"
    "--TempDir"        = "s3://${aws_s3_bucket.scripts.id}/temp/"
    "--source_bucket"  = aws_s3_bucket.raw.id
    "--target_bucket"  = aws_s3_bucket.processed.id
    "--enable-metrics" = "true"
  }

  glue_version      = "4.0"
  number_of_workers = 2
  worker_type       = "G.1X"
  timeout           = 30

  tags = {
    Name = "${local.name_prefix}-transform-orders"
  }

  depends_on = [aws_s3_object.glue_script_transform]
}

resource "aws_glue_job" "aggregation" {
  name     = "${local.name_prefix}-aggregation"
  role_arn = local.lab_role_arn

  command {
    name            = "glueetl"
    script_location = "s3://${aws_s3_bucket.scripts.id}/glue/aggregation.py"
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
  timeout           = 30

  tags = {
    Name = "${local.name_prefix}-aggregation"
  }

  depends_on = [aws_s3_object.glue_script_aggregation]
}
