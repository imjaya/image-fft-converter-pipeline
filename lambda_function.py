# -*- coding: utf-8 -*-
"""AWS Lambda function handler for an image processing pipeline."""

import logging
import os
import tempfile
from typing import Any, Dict

import boto3

from fft_tool import compute_fft  # Ensure this import is correct

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

s3 = boto3.client("s3")


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, str]:
    """Entry point for AWS Lambda triggered by S3 events.

    Args:
        event: The event dictionary provided by AWS when an S3 object
            is created.
        context: AWS Lambda context object with runtime information.

    Returns:
        A dictionary with a status message indicating completion.

    """
    # Iterate over all received S3 notifications
    for record in event.get("Records", []):
        try:
            bucket = record["s3"]["bucket"]["name"]
            key = record["s3"]["object"]["key"]

            # Only process files placed in the input/ prefix
            if not key.startswith("input/"):
                logger.info(
                    "Skipping file %s as it is not in input/ prefix", key
                )
                continue

            if not key.lower().endswith(".png"):
                logger.warning(
                    "Skipping file %s as it is not a PNG file.", key
                )
                continue

            basename = os.path.basename(key)
            logger.info("Processing %s in bucket %s", key, bucket)
            with tempfile.TemporaryDirectory() as tmpdir:
                in_path = os.path.join(tmpdir, basename)
                out_path = os.path.join(tmpdir, f"fft-{basename}")

                s3.download_file(bucket, key, in_path)
                compute_fft(in_path, out_path)

                # Upload the generated FFT image under the output/ prefix
                out_key = f"output/fft-{basename}"
                s3.upload_file(out_path, bucket, out_key)
                logger.info("Successfully processed %s to %s", key, out_key)

        except Exception as e:
            logger.error(
                "Error processing record %s: %s", record, e, exc_info=True
            )

    return {"status": "done"}
