variable "lambdaVar" {
  type = map(any)
  default = {
    function_name     = "AWS-DMS-Alert"
    #kms_key_id  = "your_kms_arn"
    TEAMS_WEBHOOK_URL = "your_teams_webhook"
}
}

variable "region" {
  type    = string
  default = "us-east-1"
}
