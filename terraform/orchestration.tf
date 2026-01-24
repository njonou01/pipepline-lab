
resource "aws_sfn_state_machine" "etl_pipeline" {
  name     = "${local.name_prefix}-etl-pipeline"
  role_arn = local.lab_role_arn

  definition = jsonencode({
    Comment = "Pipeline ETL: Raw -> Processed -> Curated"
    StartAt = "TransformOrders"
    States = {
      TransformOrders = {
        Type     = "Task"
        Resource = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = {
          JobName = aws_glue_job.transform_orders.name
        }
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "HandleError"
        }]
        Next = "Aggregation"
      }

      Aggregation = {
        Type     = "Task"
        Resource = "arn:aws:states:::glue:startJobRun.sync"
        Parameters = {
          JobName = aws_glue_job.aggregation.name
        }
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "HandleError"
        }]
        Next = "UpdateCatalog"
      }

      UpdateCatalog = {
        Type     = "Task"
        Resource = "arn:aws:states:::aws-sdk:glue:startCrawler"
        Parameters = {
          Name = aws_glue_crawler.processed.name
        }
        Catch = [{
          ErrorEquals = ["States.ALL"]
          Next        = "Success"
        }]
        Next = "Success"
      }

      HandleError = {
        Type  = "Fail"
        Error = "PipelineError"
        Cause = "ETL pipeline failed"
      }

      Success = {
        Type = "Succeed"
      }
    }
  })

  logging_configuration {
    log_destination        = "${aws_cloudwatch_log_group.stepfunctions.arn}:*"
    include_execution_data = true
    level                  = "ERROR"
  }

  tags = {
    Name = "${local.name_prefix}-etl-pipeline"
  }
}

resource "aws_cloudwatch_event_rule" "daily_etl" {
  name                = "${local.name_prefix}-daily-etl"
  description         = "Trigger ETL pipeline daily"
  schedule_expression = "cron(0 6 * * ? *)"

  tags = {
    Name = "${local.name_prefix}-daily-etl"
  }
}

resource "aws_cloudwatch_event_target" "etl_pipeline" {
  rule      = aws_cloudwatch_event_rule.daily_etl.name
  target_id = "etl-pipeline"
  arn       = aws_sfn_state_machine.etl_pipeline.arn
  role_arn  = local.lab_role_arn
}

resource "aws_cloudwatch_log_group" "stepfunctions" {
  name              = "/aws/stepfunctions/${local.name_prefix}"
  retention_in_days = 14

  tags = {
    Name = "${local.name_prefix}-stepfunctions-logs"
  }
}

resource "aws_cloudwatch_log_group" "firehose" {
  name              = "/aws/firehose/${local.name_prefix}"
  retention_in_days = 7

  tags = {
    Name = "${local.name_prefix}-firehose-logs"
  }
}

resource "aws_cloudwatch_log_stream" "firehose" {
  name           = "delivery"
  log_group_name = aws_cloudwatch_log_group.firehose.name
}
