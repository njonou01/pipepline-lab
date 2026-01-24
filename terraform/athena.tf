
resource "aws_athena_workgroup" "main" {
  name = "${local.name_prefix}-workgroup"

  configuration {
    enforce_workgroup_configuration    = true
    publish_cloudwatch_metrics_enabled = true

    result_configuration {
      output_location = "s3://${aws_s3_bucket.curated.id}/athena-results/"

      encryption_configuration {
        encryption_option = "SSE_S3"
      }
    }

    engine_version {
      selected_engine_version = "Athena engine version 3"
    }
  }

  tags = {
    Name = "${local.name_prefix}-workgroup"
  }
}

resource "aws_athena_named_query" "daily_sales" {
  name        = "daily-sales"
  description = "Daily sales report"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    SELECT
      DATE(order_date) as order_day,
      COUNT(*) as total_orders,
      SUM(total_amount) as revenue
    FROM processed_orders
    GROUP BY DATE(order_date)
    ORDER BY order_day DESC
  EOF
}

resource "aws_athena_named_query" "top_products" {
  name        = "top-products"
  description = "Top products by revenue"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    SELECT
      product_id,
      COUNT(*) as orders,
      SUM(total_amount) as revenue
    FROM processed_orders
    GROUP BY product_id
    ORDER BY revenue DESC
    LIMIT 10
  EOF
}
