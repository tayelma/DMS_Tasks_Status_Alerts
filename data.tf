data "aws_caller_identity" "dms" {}

data "archive_file" "dms_hubtel" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/lambda_function.zip"
}
