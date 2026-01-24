
data "archive_file" "trigger_pipeline" {
  type        = "zip"
  output_path = "${path.module}/builds/trigger_pipeline.zip"

  source {
    content  = <<-PYTHON
import json
import boto3
import os

def handler(event, context):
    sfn = boto3.client('stepfunctions')
    state_machine_arn = os.environ['STATE_MACHINE_ARN']

    for record in event.get('Records', []):
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        print(f"New file: s3://{bucket}/{key}")

        sfn.start_execution(
            stateMachineArn=state_machine_arn,
            input=json.dumps({'bucket': bucket, 'key': key})
        )

    return {'statusCode': 200}
PYTHON
    filename = "lambda_function.py"
  }
}

resource "aws_lambda_function" "trigger_pipeline" {
  filename         = data.archive_file.trigger_pipeline.output_path
  function_name    = "${local.name_prefix}-trigger-pipeline"
  role             = local.lab_role_arn
  handler          = "lambda_function.handler"
  source_code_hash = data.archive_file.trigger_pipeline.output_base64sha256
  runtime          = "python3.11"
  timeout          = 30

  environment {
    variables = {
      STATE_MACHINE_ARN = aws_sfn_state_machine.etl_pipeline.arn
    }
  }

  tags = {
    Name = "${local.name_prefix}-trigger-pipeline"
  }
}

resource "aws_lambda_permission" "s3_trigger" {
  statement_id  = "AllowS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.trigger_pipeline.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.raw.arn
}

resource "aws_s3_bucket_notification" "raw_trigger" {
  bucket = aws_s3_bucket.raw.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.trigger_pipeline.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "orders/"
    filter_suffix       = ".json"
  }

  depends_on = [aws_lambda_permission.s3_trigger]
}

data "archive_file" "kinesis_producer" {
  type        = "zip"
  output_path = "${path.module}/builds/kinesis_producer.zip"

  source {
    content  = <<-PYTHON
import json
import boto3
import os
import uuid
import random
from datetime import datetime

def handler(event, context):
    kinesis = boto3.client('kinesis')
    stream = os.environ['STREAM_NAME']
    count = event.get('count', 10)

    for _ in range(count):
        data = {
            'event_id': str(uuid.uuid4()),
            'type': random.choice(['view', 'cart', 'purchase']),
            'user_id': f"user_{random.randint(1, 100)}",
            'product_id': f"prod_{random.randint(1, 50)}",
            'timestamp': datetime.utcnow().isoformat()
        }
        kinesis.put_record(
            StreamName=stream,
            Data=json.dumps(data),
            PartitionKey=data['user_id']
        )

    return {'statusCode': 200, 'body': f'{count} events sent'}
PYTHON
    filename = "lambda_function.py"
  }
}

resource "aws_lambda_function" "kinesis_producer" {
  filename         = data.archive_file.kinesis_producer.output_path
  function_name    = "${local.name_prefix}-kinesis-producer"
  role             = local.lab_role_arn
  handler          = "lambda_function.handler"
  source_code_hash = data.archive_file.kinesis_producer.output_base64sha256
  runtime          = "python3.11"
  timeout          = 60

  environment {
    variables = {
      STREAM_NAME = aws_kinesis_stream.events.name
    }
  }

  tags = {
    Name = "${local.name_prefix}-kinesis-producer"
  }
}
