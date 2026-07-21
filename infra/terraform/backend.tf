# Remote state (S3 + DynamoDB lock table). Fill in once the bootstrap
# bucket/table exist — see README.md. Left commented out so `terraform init`
# defaults to local state until then.

# terraform {
#   backend "s3" {
#     bucket         = "afridock-terraform-state"
#     key            = "afridock/terraform.tfstate"
#     region         = "af-south-1"
#     dynamodb_table = "afridock-terraform-locks"
#     encrypt        = true
#   }
# }
