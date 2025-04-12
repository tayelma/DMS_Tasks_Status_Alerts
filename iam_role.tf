resource "aws_iam_role" "dms" {
  name = "${var.lambdaVar["function_name"]}-lambdaRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [{
      Action = "sts:AssumeRole",
      Effect = "Allow",
      Principal = {
        Service = "lambda.amazonaws.com"
      }
    }]
  })

  tags = {
    Name = "${var.lambdaVar["function_name"]}-lambdaRole"
  }
}

resource "aws_iam_policy" "dms" {
  name = "${var.lambdaVar["function_name"]}-lambdaPolicy"

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ],
        Effect   = "Allow",
        Resource = "arn:aws:logs:${var.region}:${data.aws_caller_identity.dms.account_id}:log-group:/aws/lambda/${var.lambdaVar["function_name"]}:*"
      },
      {
        Action = [
          "dms:DescribeReplicationTasks"
        ],
        Effect   = "Allow",
        Resource = "*"
      }
    ]
  })

  tags = {
    Name = "${var.lambdaVar["function_name"]}-lambdaPolicy"
  }
}


resource "aws_iam_role_policy_attachment" "dms" {
  role       = aws_iam_role.dms.name
  policy_arn = aws_iam_policy.dms.arn
}
