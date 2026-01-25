
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

resource "aws_athena_named_query" "trending_keywords" {
  name        = "trending-keywords"
  description = "Top trending keywords today"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    SELECT
      keyword,
      mentions,
      sources_count
    FROM trending_keywords
    WHERE date = CURRENT_DATE
    ORDER BY mentions DESC
    LIMIT 50
  EOF
}

resource "aws_athena_named_query" "volume_by_source" {
  name        = "volume-by-source"
  description = "Daily post volume by source"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    SELECT
      date,
      source,
      total_posts,
      unique_posts
    FROM volume_by_source
    WHERE date >= DATE_ADD('day', -7, CURRENT_DATE)
    ORDER BY date DESC, total_posts DESC
  EOF
}

resource "aws_athena_named_query" "trending_categories" {
  name        = "trending-categories"
  description = "Trending tech categories"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    SELECT
      category,
      SUM(mentions) as total_mentions,
      COUNT(DISTINCT date) as days_active
    FROM trending_categories
    WHERE date >= DATE_ADD('day', -7, CURRENT_DATE)
    GROUP BY category
    ORDER BY total_mentions DESC
    LIMIT 20
  EOF
}

resource "aws_athena_named_query" "search_keyword" {
  name        = "search-keyword"
  description = "Search mentions of a specific keyword"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    -- Replace 'python' with your keyword
    SELECT
      date,
      mentions,
      sources_count
    FROM trending_keywords
    WHERE keyword = 'python'
    ORDER BY date DESC
    LIMIT 30
  EOF
}

resource "aws_athena_named_query" "raw_bluesky_sample" {
  name        = "raw-bluesky-sample"
  description = "Sample raw Bluesky posts"
  workgroup   = aws_athena_workgroup.main.id
  database    = aws_glue_catalog_database.main.name

  query = <<-EOF
    SELECT
      id,
      content,
      author,
      collected_at,
      keywords,
      categories,
      is_remapped
    FROM raw_bluesky
    LIMIT 100
  EOF
}
