"""AWS Rekognition DetectLabels client and response normalization helpers."""

import boto3
from botocore.exceptions import BotoCoreError, ClientError, NoCredentialsError


class RekognitionError(Exception):
    """Raised for Rekognition failures with a user-friendly message."""


def get_client(region_name: str = "ap-south-1"):
    """Create a Rekognition client using boto3's standard credential chain."""
    try:
        return boto3.client("rekognition", region_name=region_name)
    except (BotoCoreError, NoCredentialsError) as exc:
        raise RekognitionError(
            "AWS credentials not found. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, "
            "and AWS_DEFAULT_REGION in .env, or configure an AWS profile."
        ) from exc


def detect_labels(
    image_bytes: bytes,
    region_name: str = "ap-south-1",
    max_labels: int = 1000,
    min_confidence: float = 20.0,
) -> dict:
    """Call Amazon Rekognition DetectLabels with the uploaded image bytes."""
    client = get_client(region_name)
    try:
        return client.detect_labels(
            Image={"Bytes": image_bytes},
            MaxLabels=max_labels,
            MinConfidence=min_confidence,
            Features=["GENERAL_LABELS"],
        )
    except ClientError as exc:
        error_code = exc.response.get("Error", {}).get("Code", "Unknown")
        if error_code == "InvalidImageFormatException":
            raise RekognitionError("Please upload a valid JPG or PNG image.") from exc
        if error_code == "ImageTooLargeException":
            raise RekognitionError("Image is too large for a single scan. Please use a smaller image.") from exc
        if error_code in ("UnrecognizedClientException", "AccessDeniedException"):
            raise RekognitionError(
                "AWS rejected these credentials or permissions. Ensure your IAM user has "
                "the `rekognition:DetectLabels` permission."
            ) from exc
        raise RekognitionError(f"AWS Rekognition error: {exc}") from exc
    except BotoCoreError as exc:
        raise RekognitionError(f"Could not reach AWS Rekognition: {exc}") from exc


def flatten_instances(rekognition_response: dict) -> list[dict]:
    """Convert the grouped DetectLabels response into one row per detection."""
    rows = []
    for label in rekognition_response.get("Labels", []):
        instances = label.get("Instances", [])
        parents = [parent["Name"] for parent in label.get("Parents", [])]
        if instances:
            for instance in instances:
                rows.append(
                    {
                        "label": label["Name"],
                        "confidence": round(instance["Confidence"], 1),
                        "box": instance.get("BoundingBox"),
                        "parents": parents,
                    }
                )
        else:
            rows.append(
                {
                    "label": label["Name"],
                    "confidence": round(label["Confidence"], 1),
                    "box": None,
                    "parents": parents,
                }
            )
    return rows
