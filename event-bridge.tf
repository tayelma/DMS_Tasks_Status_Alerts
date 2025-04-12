resource "aws_cloudwatch_event_rule" "dms" {
  name        = "dms_replication_tasks_event_rule"
  description = "Event rule to notify replication tasks statuses"
  event_pattern = jsonencode({
  "source": ["aws.dms"],
  "detail-type": ["DMS Replication Task State Change"],
  })

  tags = {
    Name = "${var.lambdaVar["function_name"]}-EventRule"
  }
}

resource "aws_cloudwatch_event_target" "dms" {
  rule      = aws_cloudwatch_event_rule.dms.name
  target_id = "lambda"
  arn       = aws_lambda_function.dms_function.arn
}
