
resource "aws_kinesis_stream" "events" {
  name             = "${local.name_prefix}-events"
  shard_count      = 1
  retention_period = 24

  stream_mode_details {
    stream_mode = "PROVISIONED"
  }

  encryption_type = "KMS"
  kms_key_id      = "alias/aws/kinesis"

  tags = {
    Name = "${local.name_prefix}-events"
  }
}

resource "aws_kinesis_firehose_delivery_stream" "events_to_s3" {
  name        = "${local.name_prefix}-events-to-s3"
  destination = "extended_s3"

  kinesis_source_configuration {
    kinesis_stream_arn = aws_kinesis_stream.events.arn
    role_arn           = local.lab_role_arn
  }

  extended_s3_configuration {
    role_arn            = local.lab_role_arn
    bucket_arn          = aws_s3_bucket.raw.arn
    prefix              = "events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/"
    error_output_prefix = "events-errors/!{firehose:error-output-type}/"
    buffering_size      = 5
    buffering_interval  = 60

    cloudwatch_logging_options {
      enabled         = true
      log_group_name  = aws_cloudwatch_log_group.firehose.name
      log_stream_name = aws_cloudwatch_log_stream.firehose.name
    }
  }

  tags = {
    Name = "${local.name_prefix}-events-to-s3"
  }
}
