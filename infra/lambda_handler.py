"""
Lambda handler for periodically generating and uploading the iCalendar file to S3.
"""

import json
import logging
import os
import sys

import boto3

# Add parent directory to path to import bbical module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bbical.__main__ import generate_ics_content

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def lambda_handler(event, context):
    """
    Lambda handler that generates the iCalendar file and uploads it to S3.

    Environment Variables:
        ICS_BUCKET_NAME: S3 bucket name where the .ics file will be stored
    """
    try:
        bucket_name = os.environ.get("ICS_BUCKET_NAME")
        if not bucket_name:
            raise ValueError("ICS_BUCKET_NAME environment variable not set")

        object_key = "buckhead_butcher_classes.ics"

        logger.info("Generating iCalendar content...")
        ics_content = generate_ics_content()

        if ics_content is None:
            logger.warning("No events found, skipping S3 upload")
            return {
                "statusCode": 200,
                "body": json.dumps({"message": "No events found"}),
            }

        logger.info(f"Uploading to s3://{bucket_name}/{object_key}")
        s3_client.put_object(
            Bucket=bucket_name,
            Key=object_key,
            Body=ics_content,
            ContentType="text/calendar",
        )

        logger.info("Successfully generated and uploaded iCalendar file")
        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "iCalendar file generated and uploaded successfully",
                    "bucket": bucket_name,
                    "key": object_key,
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error generating iCalendar file: {str(e)}", exc_info=True)
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }


if __name__ == "__main__":
    # For local testing
    os.environ["ICS_BUCKET_NAME"] = "test-bucket"
    result = lambda_handler({}, None)
    print(json.dumps(result, indent=2))
