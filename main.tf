#creating infrastructure for lambda function code
resource "aws_lambda_function" "dms_function" {
  function_name    = var.lambdaVar["function_name"]
  handler          = "lambda_function.lambda_handler"
 #kms_key_arn = var.lambdaVar["kms_key_id"]
  memory_size      = 128
  package_type     = "Zip"
  role             = aws_iam_role.dms.arn
  runtime          = "python3.12"
  skip_destroy     = false
  filename         = "lambda_function.zip"
  source_code_hash = data.archive_file.dms_hubtel.output_base64sha256

  tracing_config {
    mode = "Active"
  }

  environment {
    variables = {
      TEAMS_WEBHOOK_URL = var.lambdaVar["TEAMS_WEBHOOK_URL"]
    }
  }

  logging_config {
    log_format = "Text"
    log_group  = aws_cloudwatch_log_group.dms_hubtel.name
  }

  tags = {
    Name = "${var.lambdaVar["function_name"]}-Function"
  }

  depends_on = [
    aws_cloudwatch_log_group.dms_hubtel,
  ]
}

resource "aws_cloudwatch_log_group" "dms_hubtel" {
  name              = "/aws/lambda/${var.lambdaVar["function_name"]}"
  retention_in_days = 1
 #kms_key_id =  var.lambdaVar["kms_key_id"]

  tags = {
    Name = "${var.lambdaVar["function_name"]}-Lambda-LogGroup"
  }
}

