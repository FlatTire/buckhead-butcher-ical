# buckhead-butcher-ical

A Python web scraper that automatically generates iCalendar (`.ics`) files from the Buckhead Butcher Shop website and serves them via AWS infrastructure. The calendar is updated automatically 4 times per day via AWS Lambda and EventBridge.

## Features

- **Automated Web Scraping**: Extracts event details from the Buckhead Butcher Shop website
- **iCalendar Generation**: Creates RFC 5545 compliant `.ics` files for calendar applications
- **AWS Lambda Integration**: Serverless function triggered on a configurable schedule
- **EventBridge Automation**: Default schedule of 4 times per day (every 6 hours)
- **S3 Hosting**: Generated calendar file is stored in S3 and served via CloudFront CDN
- **Custom Domain**: Available at `https://buckheadbutcher.noqa.io/buckhead_butcher_classes.ics`
- **Timezone Support**: All times converted to US/Eastern timezone
- **Error Handling**: Graceful degradation when events are missing or parsing fails

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EventBridge Rule                         │
│              (cron: every 6 hours)                         │
└────────────────────────┬────────────────────────────────────┘
                         │ triggers
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  AWS Lambda Function                        │
│          (buckhead-butcher-ical-generator)                 │
│                                                             │
│  1. Scrapes buckheadbutchershop.com/classes-events/       │
│  2. Extracts event details (title, date, time, location)  │
│  3. Generates iCalendar content                           │
│  4. Uploads to S3                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                      S3 Bucket                              │
│     (noqa.io-site-20260402160936947900000003)             │
│     buckhead_butcher_classes.ics (31.7 KB)                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  CloudFront CDN                             │
│             (Global content distribution)                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Route53 DNS Records                            │
│     buckheadbutcher.noqa.io (A + AAAA alias records)      │
└─────────────────────────────────────────────────────────────┘
```

## Prerequisites

### For Local Development

- Python 3.12+
- [uv](https://docs.astral.sh/uv/) - Fast Python package installer
- Git

### For AWS Deployment

- AWS Account with appropriate permissions
- [Terraform](https://www.terraform.io/) >= 1.0
- [AWS CLI](https://aws.amazon.com/cli/) configured with credentials
- AWS Profile configured with access to S3, Lambda, IAM, EventBridge, ACM, CloudFront, and Route53

## Getting Started

### Installation

```bash
# Clone the repository
git clone <repo-url>
cd buckhead-butcher-ical

# Install dependencies
make dev

# Verify installation
make check
```

### Running Locally

Generate the calendar file locally:

```bash
# Scrape events and generate buckhead_butcher_classes.ics
make scrape

# View the generated file
cat buckhead_butcher_classes.ics | head -30
```

## Deployment

### Initial Setup (One-Time)

1. **Configure AWS credentials**:
   ```bash
   aws configure --profile personal
   # Enter: Access Key ID, Secret Access Key, Region (us-east-1), Output (json)
   ```

2. **Initialize Terraform**:
   ```bash
   make tf-init
   ```

3. **Review infrastructure plan**:
   ```bash
   AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 make tf-plan
   ```

### Deploying Infrastructure

```bash
# Build Lambda deployment package with dependencies
make lambda-package

# Plan Terraform changes (review before applying)
AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 make tf-plan

# Deploy infrastructure
AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 make tf-apply
```

### What Gets Deployed

- **S3 Bucket**: Auto-generated name with `noqa.io-site-` prefix
- **CloudFront Distribution**: CDN with caching strategies for different file types
- **Route53 DNS Records**: A and AAAA alias records pointing to CloudFront
- **ACM Certificate**: HTTPS/TLS with automatic DNS validation
- **Lambda Function**: `buckhead-butcher-ical-generator` with Python 3.12 runtime
- **IAM Role & Policy**: Permissions for Lambda to write to S3 and create logs
- **EventBridge Rule**: Scheduled trigger (default: `cron(0 */6 * * ? *)`)

### Customizing the Schedule

Edit `infra/variables.tf` to change the EventBridge schedule expression:

```hcl
variable "ical_schedule_expression" {
  description = "EventBridge cron expression for iCal generation schedule"
  type        = string
  default     = "cron(0 */6 * * ? *)"  # Modify this
}
```

Common patterns:
- **Every 6 hours (4x/day)**: `cron(0 */6 * * ? *)`
- **Every 4 hours (6x/day)**: `cron(0 */4 * * ? *)`
- **Every 2 hours (12x/day)**: `cron(0 */2 * * ? *)`
- **Hourly**: `cron(0 * * * ? *)`
- **Daily at 9am UTC**: `cron(0 9 * * ? *)`

Then re-apply: `AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 make tf-apply`

## Usage

### Accessing the Calendar

**Public URL**: `https://buckheadbutcher.noqa.io/buckhead_butcher_classes.ics`

### Subscribing in Calendar Applications

#### Google Calendar
1. Open Google Calendar
2. Click "+" next to "Other calendars"
3. Select "Subscribe to calendar"
4. Paste: `https://buckheadbutcher.noqa.io/buckhead_butcher_classes.ics`
5. Click "Subscribe"

#### Apple Calendar
1. Open Calendar app
2. File → New Calendar Subscription
3. Paste: `https://buckheadbutcher.noqa.io/buckhead_butcher_classes.ics`
4. Click "Subscribe"

#### Outlook
1. Open Outlook
2. File → Open & Export → Import ICS
3. Or use: Add calendar → Subscribe from web
4. Paste: `https://buckheadbutcher.noqa.io/buckhead_butcher_classes.ics`

### Manual Invocation

Trigger the Lambda function manually without waiting for the schedule:

```bash
AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 aws lambda invoke \
  --function-name buckhead-butcher-ical-generator \
  response.json

cat response.json
```

### Checking Logs

View Lambda execution logs:

```bash
AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 aws logs tail \
  /aws/lambda/buckhead-butcher-ical-generator --follow
```

## Testing & Quality Assurance

### Running Tests

```bash
# Run all tests
make test

# Run tests with verbose output
uv run pytest tests -v

# Run specific test file
uv run pytest tests/test_scraper.py -v

# Run with coverage
uv run pytest tests --cov=bbical
```

### Code Quality Checks

```bash
# Lint code
make lint

# Format code (in-place)
make format

# Type checking
make type-check

# Run all checks
make check
```

### Test Coverage

The project includes comprehensive unit tests in `tests/test_scraper.py` covering:

- **Date/Time Parsing**: Various date formats and edge cases
- **Web Scraping**: Event link extraction and filtering
- **Event Details**: Data extraction and fallback handling
- **iCalendar Generation**: RFC 5545 compliance
- **Error Handling**: Graceful degradation for missing data

Run tests before committing:

```bash
make check  # Lint + type-check
make test   # Unit tests
```

## Contributing

### Development Workflow

1. **Create a branch** for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes** following project conventions:
   - Use Python 3.12+ syntax
   - Follow [PEP 8](https://pep8.org/) style guide
   - Add type hints for new functions
   - Write tests for new functionality

3. **Run checks** before committing:
   ```bash
   make format  # Auto-format code
   make check   # Lint + type-check
   make test    # Run tests
   ```

4. **Commit with conventional commits**:
   ```bash
   git commit -m "type(scope): subject

   Detailed explanation of changes if needed.
   
   - Bullet points for clarity
   - Reference issue numbers (#123) if applicable"
   ```
   
   Common types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `build`, `config`

5. **Push and create a pull request**:
   ```bash
   git push origin feature/your-feature-name
   ```

### Conventional Commits

This project follows [Conventional Commits](https://www.conventionalcommits.org/) specification:

```
type(scope): subject

body

footer
```

Examples:
- `feat(scraper): add support for multi-day events`
- `fix(parser): handle 12:00 AM edge case`
- `refactor(lambda): extract S3 upload logic`
- `docs(readme): update deployment instructions`
- `test(scraper): add tests for date parsing`

### Code Style

- **Formatter**: [ruff](https://github.com/astral-sh/ruff) - Run `make format`
- **Linter**: [ruff](https://github.com/astral-sh/ruff) - Run `make lint`
- **Type Checker**: [mypy](https://mypy.readthedocs.io/) - Run `make type-check`

### Adding Dependencies

Use `uv` to add new dependencies:

```bash
uv add requests-cache          # Add to production
uv add --dev pytest-mock       # Add to dev dependencies
```

Then sync your environment:

```bash
uv sync
```

## Project Structure

```
buckhead-butcher-ical/
├── bbical/                          # Main Python package
│   ├── __init__.py
│   └── __main__.py                  # Scraper & iCal generator
├── tests/
│   ├── __init__.py
│   └── test_scraper.py             # Comprehensive test suite
├── infra/                           # Infrastructure as Code
│   ├── main.tf                      # AWS resources (S3, Lambda, EventBridge, etc.)
│   ├── variables.tf                 # Terraform input variables
│   ├── outputs.tf                   # Terraform outputs
│   ├── lambda_handler.py            # Lambda function entry point
│   └── .gitignore
├── docs/
│   └── TERRAFORM_STATE_SETUP.md    # S3 state backend configuration
├── pyproject.toml                   # Python project metadata & dependencies
├── uv.lock                          # Dependency lock file (auto-generated)
├── Makefile                         # Build and deployment targets
├── README.md                        # This file
└── buckhead_butcher_classes.ics    # Generated calendar (not committed)
```

## How It Works

### Local Execution Flow

1. **Scraping**: `scrape_event_links()` fetches the classes page and extracts event URLs
2. **Parsing**: For each event:
   - `scrape_event_details()` extracts title, date, time, location, description
   - `parse_date_time()` converts human-readable dates to timezone-aware datetime objects
3. **Generation**: `create_ical()` builds an RFC 5545 compliant calendar
4. **Output**: Calendar is written to `buckhead_butcher_classes.ics`

### Lambda Execution Flow

1. **Trigger**: EventBridge rule fires on schedule
2. **Invocation**: Lambda function `lambda_handler()` is called
3. **Execution**: Same scraping logic runs, but instead of writing to disk:
   - `generate_ics_content()` returns iCalendar bytes
   - `lambda_handler()` uploads to S3 using boto3
4. **CloudFront**: CDN automatically caches the updated file
5. **Logging**: Execution logged to CloudWatch

## Troubleshooting

### Lambda function fails with "ICS_BUCKET_NAME not set"

**Cause**: Environment variable not configured

**Fix**: Re-deploy with Terraform:
```bash
AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 make tf-plan
AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 make tf-apply
```

### Calendar file not updating

**Check**:
1. Manual Lambda invocation:
   ```bash
   AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 aws lambda invoke \
     --function-name buckhead-butcher-ical-generator response.json
   cat response.json
   ```

2. Check CloudWatch logs:
   ```bash
   AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 aws logs tail \
     /aws/lambda/buckhead-butcher-ical-generator
   ```

3. Verify S3 file exists:
   ```bash
   AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 aws s3 ls \
     s3://noqa.io-site-20260402160936947900000003/
   ```

4. Check EventBridge rule status:
   ```bash
   AWS_PROFILE=personal AWS_DEFAULT_REGION=us-east-1 aws events \
     describe-rule --name buckhead-butcher-ical-schedule
   ```

### Tests fail with "Could not parse date"

**Cause**: Website HTML structure changed

**Fix**: 
1. Update regex patterns in `bbical/__main__.py`
2. Run `make test` to verify
3. Commit changes with conventional commits

### Terraform plan shows unexpected changes

**Common cause**: Out-of-date state or local changes

**Fix**:
```bash
cd infra
terraform refresh
terraform plan -out=tfplan
# Review the plan before applying
```

## Monitoring & Maintenance

### Regular Checks

- **Weekly**: Verify calendar updates appear in your calendar app
- **Monthly**: Review CloudWatch logs for errors or warnings
- **Quarterly**: Test website scraping if the Buckhead Butcher Shop updates their site structure

### CloudWatch Metrics

Lambda metrics available in AWS CloudWatch:
- Invocations
- Duration
- Errors
- Throttles

### CloudFront Analytics

CloudFront distribution provides:
- Request counts
- Data transfer metrics
- Cache hit ratio

Access in AWS Console: CloudFront → Distributions → Buckhead Butcher iCal

## Performance & Costs

### Lambda

- **Cost**: ~$0.20/million invocations + $0.0000166667/GB-second
- **Typical execution**: 5-10 seconds per run
- **Monthly cost**: ~$0.01-0.05 (minimal)

### S3

- **Cost**: ~$0.023/GB stored + request charges
- **File size**: ~32 KB
- **Monthly cost**: <$0.01

### CloudFront

- **Cost**: Varies by region ($0.085/GB for US, Europe)
- **Typical traffic**: <1 GB/month for calendar
- **Monthly cost**: <$0.10

**Total estimated monthly cost**: <$0.20

## License

[Add appropriate license]

## Contact & Support

For issues, questions, or suggestions:
- Open a GitHub issue
- Check existing issues for similar problems
- Review logs and troubleshooting section above

## Changelog

See `git log` for detailed commit history.

### Recent Releases

- **v1.0.0** (2026-04-02): Initial release with Lambda automation
  - Automated iCalendar generation via Lambda
  - EventBridge scheduling (4x per day)
  - CloudFront CDN distribution
  - Route53 DNS integration
