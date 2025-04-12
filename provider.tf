terraform {

  required_providers {
    aws = {
      source = "hashicorp/aws"
      version = "5.63.0"
    }
  }

  backend "s3" {
    bucket = "states-tf-projects"
    key    = "DMSTasksAlarms/terraform.tfstate"
    region = "us-east-1"
    profile = "misscloud"
  }
}


provider "aws" {
  region = var.region
  profile = "misscloud"
}