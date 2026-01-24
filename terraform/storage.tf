
resource "aws_s3_bucket" "raw" {
  bucket = "${local.bucket_prefix}-raw"

  tags = {
    Name = "${local.name_prefix}-raw"
    Zone = "raw"
  }
}

resource "aws_s3_bucket_versioning" "raw" {
  bucket = aws_s3_bucket.raw.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "raw" {
  bucket = aws_s3_bucket.raw.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "raw" {
  bucket                  = aws_s3_bucket.raw.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "processed" {
  bucket = "${local.bucket_prefix}-processed"

  tags = {
    Name = "${local.name_prefix}-processed"
    Zone = "processed"
  }
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "processed" {
  bucket = aws_s3_bucket.processed.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "processed" {
  bucket = aws_s3_bucket.processed.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "processed" {
  bucket                  = aws_s3_bucket.processed.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "curated" {
  bucket = "${local.bucket_prefix}-curated"

  tags = {
    Name = "${local.name_prefix}-curated"
    Zone = "curated"
  }
  force_destroy = true
}

resource "aws_s3_bucket_versioning" "curated" {
  bucket = aws_s3_bucket.curated.id
  versioning_configuration {
    status = "Enabled"
  }

}

resource "aws_s3_bucket_server_side_encryption_configuration" "curated" {
  bucket = aws_s3_bucket.curated.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }

}

resource "aws_s3_bucket_public_access_block" "curated" {
  bucket                  = aws_s3_bucket.curated.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket" "scripts" {
  bucket = "${local.bucket_prefix}-scripts"

  tags = {
    Name = "${local.name_prefix}-scripts"
    Zone = "scripts"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "scripts" {
  bucket = aws_s3_bucket.scripts.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "scripts" {
  bucket                  = aws_s3_bucket.scripts.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_object" "raw_folders" {
  for_each = toset(["orders/", "customers/", "products/", "events/"])
  bucket   = aws_s3_bucket.raw.id
  key      = each.value
  content  = ""
}

resource "aws_s3_object" "processed_folders" {
  for_each = toset(["orders/", "customers/", "products/"])
  bucket   = aws_s3_bucket.processed.id
  key      = each.value
  content  = ""
}

resource "aws_s3_object" "curated_folders" {
  for_each = toset(["analytics/", "reports/"])
  bucket   = aws_s3_bucket.curated.id
  key      = each.value
  content  = ""
}

resource "aws_s3_object" "glue_script_transform" {
  bucket = aws_s3_bucket.scripts.id
  key    = "glue/orders_transform.py"
  source = "${path.module}/../scripts/glue/orders_transform.py"
  etag   = filemd5("${path.module}/../scripts/glue/orders_transform.py")
}

resource "aws_s3_object" "glue_script_aggregation" {
  bucket = aws_s3_bucket.scripts.id
  key    = "glue/aggregation.py"
  source = "${path.module}/../scripts/glue/aggregation.py"
  etag   = filemd5("${path.module}/../scripts/glue/aggregation.py")
}

resource "aws_s3_object" "sample_orders" {
  bucket = aws_s3_bucket.raw.id
  key    = "orders/sample_orders.json"
  source = "${path.module}/../data/sample/orders.json"
  etag   = filemd5("${path.module}/../data/sample/orders.json")
}

resource "aws_s3_object" "sample_customers" {
  bucket = aws_s3_bucket.raw.id
  key    = "customers/sample_customers.json"
  source = "${path.module}/../data/sample/customers.json"
  etag   = filemd5("${path.module}/../data/sample/customers.json")
}

resource "aws_s3_object" "sample_products" {
  bucket = aws_s3_bucket.raw.id
  key    = "products/sample_products.json"
  source = "${path.module}/../data/sample/products.json"
  etag   = filemd5("${path.module}/../data/sample/products.json")
}
