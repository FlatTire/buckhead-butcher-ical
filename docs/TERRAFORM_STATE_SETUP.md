# Terraform State Setup

This document describes the one-time manual setup required for the Terraform state bucket.

## Overview

The Terraform state for this project is stored in an existing S3 bucket with the following configuration:

- **Bucket**: `pe-tfstate-400331679889-us-east-1`
- **State Key**: `buckhead-butcher-ical/terraform.tfstate`
- **Region**: `us-east-1`

## One-Time Setup

### 1. Enable Versioning on the State Bucket

```bash
aws s3api put-bucket-versioning \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --versioning-configuration Status=Enabled \
  --profile personal \
  --region us-east-1
```

### 2. Set Up Lifecycle Policy

Apply the following lifecycle policy to automatically manage old state file versions:

```bash
aws s3api put-bucket-lifecycle-configuration \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --lifecycle-configuration '{
    "Rules": [
      {
        "Id": "cleanup-old-state-versions",
        "Status": "Enabled",
        "NoncurrentVersionTransitions": [
          {
            "NoncurrentDays": 90,
            "StorageClass": "GLACIER"
          }
        ],
        "NoncurrentVersionExpirations": [
          {
            "NoncurrentDays": 90
          }
        ]
      }
    ]
  }' \
  --profile personal \
  --region us-east-1
```

### 3. Verify Configuration

Check that versioning is enabled:

```bash
aws s3api get-bucket-versioning \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --profile personal \
  --region us-east-1
```

Expected output:
```json
{
    "Status": "Enabled"
}
```

Check the lifecycle policy:

```bash
aws s3api get-bucket-lifecycle-configuration \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --profile personal \
  --region us-east-1
```

## Terraform Backend Configuration

Once the bucket is configured, the following backend configuration is used in `infra/main.tf`:

```hcl
terraform {
  backend "s3" {
    bucket = "pe-tfstate-400331679889-us-east-1"
    key    = "buckhead-butcher-ical/terraform.tfstate"
    region = "us-east-1"
  }
}
```

## Backup and Recovery

### List All Versions of the State File

```bash
aws s3api list-object-versions \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --prefix buckhead-butcher-ical/ \
  --profile personal \
  --region us-east-1
```

### Restore a Previous Version

```bash
aws s3api get-object \
  --bucket pe-tfstate-400331679889-us-east-1 \
  --key buckhead-butcher-ical/terraform.tfstate \
  --version-id VERSION_ID \
  terraform.tfstate.backup \
  --profile personal \
  --region us-east-1
```

## Notes

- Versioning allows recovery from accidental state file corruption or deletion
- Old versions are transitioned to Glacier storage class after 90 days to reduce costs
- Versions are automatically deleted after 90 days (configurable)
- The S3 bucket should have public access blocked as a security best practice
- Consider enabling MFA Delete protection on the bucket for additional security
