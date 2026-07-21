variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "af-south-1"
}

variable "environment" {
  description = "Deployment environment name (staging, production)"
  type        = string
}

variable "project" {
  description = "Project name used for resource naming/tagging"
  type        = string
  default     = "afridock"
}
