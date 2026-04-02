# Buckhead Butcher Static Hosting Infrastructure

This Terraform configuration creates a secure, scalable static hosting environment using AWS S3 and CloudFront.

## Architecture

- **S3 Bucket**: Stores static site content with versioning enabled
- **CloudFront**: Global CDN with TLS 1.2+ security
- **Origin Access Identity (OAI)**: Restricts S3 access to CloudFront only
- **ACM Certificate**: HTTPS support for custom domain
- **Lifecycle Policies**: Automatic cleanup of old S3 versions

## Security Features

- ✅ TLS 1.2+ only (TLS 1.1 and 1.0 disabled)
- ✅ HTTP/2 and HTTP/3 support
- ✅ Gzip compression enabled
- ✅ S3 bucket public access blocked
- ✅ Server-side encryption (AES256) enabled
- ✅ Versioning with automatic cleanup (max 5 versions, 90 days)
- ✅ OAI for secure S3 access
- ✅ HTTP to HTTPS redirect
- ✅ SPA routing support (404 → index.html)

## Prerequisites

- Terraform >= 1.0
- AWS credentials configured with appropriate permissions
- Domain registered and accessible for DNS validation
- ACM certificate DNS validation capability

## Configuration

### Basic Setup

1. Copy the example configuration:
```bash
cp terraform.tfvars.example terraform.tfvars
```

2. Edit `terraform.tfvars` with your desired values:
```hcl
aws_region = "us-east-1"
hostname   = "buckheadbutcher.noqa.io"
domain_name = "noqa.io"
```

### Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `us-east-1` | AWS region |
| `domain_name` | `noqa.io` | Base domain name |
| `hostname` | `buckheadbutcher.noqa.io` | Full hostname for the site |
| `environment` | `production` | Environment name |
| `s3_versioning_max_versions` | `5` | Max versions to keep in S3 |
| `s3_versioning_days` | `90` | Days to keep old versions |

## Deployment

### Initialize Terraform

```bash
terraform init
```

### Plan the deployment

```bash
terraform plan -out=tfplan
```

### Apply the configuration

```bash
terraform apply tfplan
```

### Certificate Validation

After applying, you'll need to validate the ACM certificate via DNS:

1. Get the validation records:
```bash
terraform output certificate_validation_options
```

2. Add the DNS CNAME records to your domain's DNS provider

3. The certificate will be automatically validated once DNS records are in place

### DNS Configuration

Once the infrastructure is deployed, update your DNS records:

1. Create a CNAME record pointing to CloudFront:
   - Name: `buckheadbutcher.noqa.io`
   - Type: `CNAME`
   - Value: CloudFront domain name (from `terraform output cloudfront_domain_name`)

## Uploading Content

Upload your static files to the S3 bucket:

```bash
aws s3 sync ./dist/ s3://$(terraform output -raw s3_bucket_name)/ --delete
```

Or using AWS CLI:

```bash
aws s3 cp index.html s3://$(terraform output -raw s3_bucket_name)/
```

## CloudFront Cache Invalidation

After updating content, invalidate the CloudFront cache:

```bash
aws cloudfront create-invalidation \
  --distribution-id $(terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

## Outputs

After deployment, Terraform outputs:

```bash
terraform output
```

Key outputs:
- `s3_bucket_name`: S3 bucket name
- `cloudfront_distribution_id`: CloudFront distribution ID
- `cloudfront_domain_name`: CloudFront domain
- `site_url`: HTTPS URL of your site
- `certificate_arn`: ACM certificate ARN

## Cost Optimization

- Static assets (JS, CSS, fonts) are cached for 1 year
- Images are cached for 7 days
- HTML is cached for 1 hour
- S3 old versions transition to Glacier after 90 days

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

## Notes

- This configuration assumes a single CloudFront distribution for one domain
- S3 versioning is enabled with automatic lifecycle management
- The distribution supports Single Page Application (SPA) routing
- Custom error responses redirect 404 to index.html for SPA support
