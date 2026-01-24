
output "streamlit_url" {
  description = "Streamlit dashboard URL"
  value       = "http://${aws_eip.streamlit.public_ip}"
}

output "streamlit_ip" {
  description = "Streamlit Elastic IP"
  value       = aws_eip.streamlit.public_ip
}

output "ssh_command" {
  description = "SSH command to connect"
  value       = "ssh -i mykey.pem ubuntu@${aws_eip.streamlit.public_ip}"
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

output "glue_job_transform" {
  description = "Glue ETL job - Transform"
  value       = aws_glue_job.transform_orders.name
}

output "glue_job_aggregation" {
  description = "Glue ETL job - Aggregation"
  value       = aws_glue_job.aggregation.name
}

output "athena_workgroup" {
  description = "Athena workgroup"
  value       = aws_athena_workgroup.main.name
}

output "kinesis_stream" {
  description = "Kinesis stream name"
  value       = aws_kinesis_stream.events.name
}

output "step_functions_arn" {
  description = "Step Functions state machine ARN"
  value       = aws_sfn_state_machine.etl_pipeline.arn
}

output "dashboard_dns" {
  description = "Dashboard DNS name"
  value       = var.create_dns_zone ? "http://dashboard.${var.domain_name}" : null
}
