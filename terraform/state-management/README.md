# Terraform State Management

This directory contains the Terraform configuration to manage the shared state bucket and state locking infrastructure.

## Overview

- **State Bucket**: `pe-tfstate-400331679889-us-east-1`
- **State Key Prefix**: `buckhead-butcher-ical/`
- **Locking Table**: `terraform-locks` (DynamoDB)
- **Encryption**: AES256 (server-side)
- **Versioning**: Enabled with 90-day retention

## Purpose

The infrastructure in this directory manages:

1. **S3 Bucket Configuration**:
   - Versioning enabled
   - Public access blocked
   - Server-side encryption enabled
   - Lifecycle policies for old version cleanup

2. **DynamoDB Table**:
   - State locking to prevent concurrent modifications
   - Point-in-time recovery enabled

## Setup

### Prerequisites

This is typically set up once and shared across multiple Terraform projects in the organization.

### Initial Setup

```bash
cd terraform/state-management
terraform init
terraform plan
terraform apply
```

### Importing Existing Bucket (if bucket already exists)

If the S3 bucket already exists in AWS but is not managed by Terraform:

```bash
terraform import aws_s3_bucket.terraform_state pe-tfstate-400331679889-us-east-1
terraform import aws_dynamodb_table.terraform_locks terraform-locks
```

## Backend Configuration

Once the state infrastructure is set up, use the following backend configuration in other Terraform projects:

```hcl
terraform {
  backend "s3" {
    bucket         = "pe-tfstate-400331679889-us-east-1"
    key            = "buckhead-butcher-ical/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

This configuration is already in place in `infra/backend.tf`.

## State File Location

For this project, the state file is stored at:
```
s3://pe-tfstate-400331679889-us-east-1/buckhead-butcher-ical/terraform.tfstate
```

With versioning enabled, all previous versions are accessible for recovery.

## Security Features

✅ Server-side encryption enabled (AES256)
✅ Public access completely blocked
✅ Versioning enabled for state recovery
✅ DynamoDB locking prevents concurrent modifications
✅ Point-in-time recovery on DynamoDB table
✅ Lifecycle policies clean up old versions after 90 days

### MFA Delete Protection (Optional)

For maximum security, MFA Delete protection can be enabled on the bucket. This requires:
1. Root account credentials
2. MFA device serial number

To enable:
```bash
aws s3api put-bucket-versioning \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --versioning-configuration Status=Enabled,MFADelete=Enabled \
  --mfa "arn-of-mfa-device mfa-code"
```

## Backup and Recovery

### List all versions of state file

```bash
aws s3api list-object-versions \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --prefix buckhead-butcher-ical/
```

### Restore a previous version

```bash
aws s3api get-object \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --key buckhead-butcher-ical/terraform.tfstate \
  --version-id VERSION_ID \
  terraform.tfstate.backup
```

## Cleanup

To destroy this infrastructure (use with caution):

```bash
terraform destroy
```

⚠️ **Warning**: Destroying this infrastructure will:
- Delete the DynamoDB table
- NOT delete the S3 bucket (S3 bucket deletion is protected to prevent data loss)
- The S3 bucket must be manually deleted if needed

## Notes

- State files should never be stored in version control
- Always use the remote backend in production
- The S3 bucket name includes the AWS account ID for uniqueness
- Versioning ensures recovery capability for state file corruption
