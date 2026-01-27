
output "streamlit_url" {
  description = "Streamlit dashboard URL"
  value       = "http://${aws_eip.streamlit.public_ip}"
}

output "streamlit_ip" {
  description = "Streamlit Elastic IP"
  value       = aws_eip.streamlit.public_ip
}

output "streamlit_ssh" {
  description = "SSH command to connect to Streamlit"
  value       = "ssh -i mykey.pem ubuntu@${aws_eip.streamlit.public_ip}"
}

output "kafka_ip" {
  description = "Kafka Elastic IP"
  value       = aws_eip.kafka.public_ip
}

output "kafka_broker" {
  description = "Kafka broker endpoint"
  value       = "${aws_eip.kafka.public_ip}:9092"
}

output "kafka_ssh" {
  description = "SSH command to connect to Kafka"
  value       = "ssh -i mykey.pem ubuntu@${aws_eip.kafka.public_ip}"
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = "${aws_eip.kafka.public_ip}:6379"
}


output "s3_raw" {
  description = "S3 bucket - Raw zone"
  value       = aws_s3_bucket.raw.id
}

output "s3_processed" {
  description = "S3 bucket - Processed zone"
  value       = aws_s3_bucket.processed.id
}

output "s3_curated" {
  description = "S3 bucket - Curated zone"
  value       = aws_s3_bucket.curated.id
}

output "s3_scripts" {
  description = "S3 bucket - Glue scripts"
  value       = aws_s3_bucket.scripts.id
}

output "glue_database" {
  description = "Glue Catalog database"
  value       = aws_glue_catalog_database.main.name
}

output "glue_jobs_transform" {
  description = "Glue ETL jobs - Transform (one per source)"
  value       = { for k, v in aws_glue_job.transform_social : k => v.name }
}

output "glue_job_aggregation" {
  description = "Glue ETL job - Aggregation"
  value       = aws_glue_job.aggregation.name
}

output "athena_workgroup" {
  description = "Athena workgroup"
  value       = aws_athena_workgroup.main.name
}

output "step_functions_arn" {
  description = "Step Functions state machine ARN"
  value       = aws_sfn_state_machine.etl_pipeline.arn
}

output "dashboard_dns" {
  description = "Dashboard DNS name"
  value       = var.create_dns_zone ? "http://dashboard.${var.domain_name}" : null
}

output "sources" {
  description = "Data sources being collected"
  value       = ["bluesky", "nostr", "hackernews", "stackoverflow", "rss"]
}

output "sns_topic_arn" {
  description = "SNS topic ARN for pipeline alerts"
  value       = aws_sns_topic.pipeline_alerts.arn
}

output "alert_email" {
  description = "Email configured for alerts"
  value       = var.alert_email
}
