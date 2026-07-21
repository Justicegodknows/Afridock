terraform {
  required_version = ">= 1.9"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      project     = var.project
      environment = var.environment
      managed_by  = "terraform"
    }
  }
}

# Resources (VPC, ECS Fargate services, RDS Postgres, ElastiCache Redis, S3,
# ECR) land here per work package as each phase requires them — see
# Afridock_Implementation_Execution_Plan.md §2.3 and §4.
