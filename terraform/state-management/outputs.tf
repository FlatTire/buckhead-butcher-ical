output "state_bucket_name" {
  description = "Name of the Terraform state bucket"
  value       = aws_s3_bucket.terraform_state.id
}

output "state_bucket_arn" {
  description = "ARN of the Terraform state bucket"
  value       = aws_s3_bucket.terraform_state.arn
}

output "state_bucket_region" {
  description = "Region of the Terraform state bucket"
  value       = aws_s3_bucket.terraform_state.region
}

output "dynamodb_table_name" {
  description = "Name of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.name
}

output "dynamodb_table_arn" {
  description = "ARN of the DynamoDB table for state locking"
  value       = aws_dynamodb_table.terraform_locks.arn
}

output "backend_config" {
  description = "Backend configuration to use in other Terraform projects"
  value = {
    bucket         = aws_s3_bucket.terraform_state.id
    key            = "buckhead-butcher-ical/terraform.tfstate"
    region         = aws_s3_bucket.terraform_state.region
    encrypt        = true
    dynamodb_table = aws_dynamodb_table.terraform_locks.name
  }
}
