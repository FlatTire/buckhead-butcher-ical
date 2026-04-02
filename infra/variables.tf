variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "domain_name" {
  description = "Base domain name for the static site"
  type        = string
  default     = "noqa.io"
}

variable "hostname" {
  description = "Full hostname for the static site"
  type        = string
  default     = "buckheadbutcher.noqa.io"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "production"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "Buckhead Butcher"
    Environment = "production"
    ManagedBy   = "Terraform"
  }
}

variable "s3_versioning_max_versions" {
  description = "Maximum number of versions to keep in S3"
  type        = number
  default     = 5
}

variable "s3_versioning_days" {
  description = "Number of days to keep old versions in S3"
  type        = number
  default     = 90
}

variable "ical_schedule_expression" {
  description = "EventBridge cron expression for iCal generation schedule"
  type        = string
  default     = "cron(0 */6 * * ? *)"
}
