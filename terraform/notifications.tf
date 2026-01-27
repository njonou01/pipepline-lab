# ========================================
# SNS TOPICS FOR NOTIFICATIONS
# ========================================

resource "aws_sns_topic" "pipeline_alerts" {
  name = "${local.name_prefix}-pipeline-alerts"

  tags = {
    Name = "${local.name_prefix}-pipeline-alerts"
  }
}

resource "aws_sns_topic_subscription" "email_alerts" {
  topic_arn = aws_sns_topic.pipeline_alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ========================================
# CLOUDWATCH ALARMS
# ========================================

# Alarm for Step Functions failures
resource "aws_cloudwatch_metric_alarm" "step_functions_failed" {
  alarm_name          = "${local.name_prefix}-step-functions-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ExecutionsFailed"
  namespace           = "AWS/States"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when Step Functions pipeline fails"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]

  dimensions = {
    StateMachineArn = aws_sfn_state_machine.etl_pipeline.arn
  }
}

# Alarm for Glue job failures
resource "aws_cloudwatch_metric_alarm" "glue_jobs_failed" {
  alarm_name          = "${local.name_prefix}-glue-jobs-failed"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "glue.driver.aggregate.numFailedTasks"
  namespace           = "Glue"
  period              = 300
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when Glue jobs fail"
  alarm_actions       = [aws_sns_topic.pipeline_alerts.arn]
}

# ========================================
# SES EMAIL IDENTITY (Optional)
# ========================================

resource "aws_ses_email_identity" "alert_sender" {
  count = var.enable_ses ? 1 : 0
  email = var.alert_email
}

# SNS topic for SES bounce/complaint notifications
resource "aws_sns_topic" "ses_notifications" {
  count = var.enable_ses ? 1 : 0
  name  = "${local.name_prefix}-ses-notifications"

  tags = {
    Name = "${local.name_prefix}-ses-notifications"
  }
}
