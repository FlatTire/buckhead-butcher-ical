output "s3_bucket_name" {
  description = "Name of the S3 bucket"
  value       = aws_s3_bucket.site.id
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.site.arn
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.site.domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.site.id
}

output "cloudfront_distribution_arn" {
  description = "ARN of the CloudFront distribution"
  value       = aws_cloudfront_distribution.site.arn
}

output "certificate_arn" {
  description = "ARN of the ACM certificate"
  value       = aws_acm_certificate.site.arn
}

output "certificate_validation_options" {
  description = "Certificate validation options (for DNS records)"
  value       = aws_acm_certificate.site.domain_validation_options
  sensitive   = true
}

output "oai_iam_arn" {
  description = "IAM ARN of the CloudFront Origin Access Identity"
  value       = aws_cloudfront_origin_access_identity.site.iam_arn
}

output "site_url" {
  description = "URL of the static site"
  value       = "https://${var.hostname}"
}

output "cloudfront_url" {
  description = "CloudFront distribution URL"
  value       = "https://${aws_cloudfront_distribution.site.domain_name}"
}

output "lambda_function_arn" {
  description = "ARN of the Lambda function for generating iCalendar"
  value       = aws_lambda_function.ical_generator.arn
}

output "lambda_function_name" {
  description = "Name of the Lambda function"
  value       = aws_lambda_function.ical_generator.function_name
}

output "eventbridge_rule_arn" {
  description = "ARN of the EventBridge rule for scheduling"
  value       = aws_cloudwatch_event_rule.ical_schedule.arn
}

output "ical_s3_location" {
  description = "S3 location of the generated iCalendar file"
  value       = "s3://${aws_s3_bucket.site.id}/buckhead_butcher_classes.ics"
}

output "ical_public_url" {
  description = "Public URL to access the iCalendar file"
  value       = "https://${var.hostname}/buckhead_butcher_classes.ics"
}
