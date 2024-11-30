import logging
from dataclasses import dataclass
from typing import Any
from typing import Dict

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def assert_settings(required_settings, error_message_prefix=""):
    """
    Checks if each item from `required_settings` is present in Django settings
    """
    not_present = []
    values = {}

    for required_setting in required_settings:
        if not hasattr(settings, required_setting):
            not_present.append(required_setting)
            continue

        values[required_setting] = getattr(settings, required_setting)

    if not_present:
        if not error_message_prefix:
            error_message_prefix = "Required settings not found."

        stringified_not_present = ", ".join(not_present)

        raise ImproperlyConfigured(
            f"{error_message_prefix} Could not find: {stringified_not_present}"
        )

    return values


@dataclass()
class S3Credentials:
    access_key_id: str
    secret_access_key: str
    region_name: str
    bucket_name: str
    default_acl: str
    presigned_expiry: int
    max_size: int


def s3_get_credentials() -> S3Credentials:
    required_config = assert_settings(
        [
            "AWS_ACCESS_KEY_ID",
            "AWS_SECRET_ACCESS_KEY",
            "AWS_S3_REGION_NAME",
            "AWS_STORAGE_BUCKET_NAME",
            "AWS_DEFAULT_ACL",
            "AWS_PRESIGNED_EXPIRY",
            "FILE_MAX_SIZE",
            "FILE_UPLOAD_STORAGE",
            "ALLOW_AUTHENTICATION",
            "APP_DOMAIN",
            "IS_USING_LOCAL_STORAGE",
            "MEDIA_LOCATION"
        ],
        "S3 credentials not found.",
    )

    return S3Credentials(
        access_key_id=required_config["AWS_ACCESS_KEY_ID"],
        secret_access_key=required_config["AWS_SECRET_ACCESS_KEY"],
        region_name=required_config["AWS_S3_REGION_NAME"],
        bucket_name=required_config["AWS_STORAGE_BUCKET_NAME"],
        default_acl=required_config["AWS_DEFAULT_ACL"],
        presigned_expiry=required_config["AWS_PRESIGNED_EXPIRY"],
        max_size=required_config["FILE_MAX_SIZE"],
    )


def s3_get_client():
    credentials = s3_get_credentials()

    return boto3.client(
        service_name="s3",
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        region_name=credentials.region_name,
    )


def s3_resource_client():
    credentials = s3_get_credentials()

    return boto3.resource(
        service_name="s3",
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        region_name=credentials.region_name,
    )


def s3_generate_presigned_post(
    *, file_path: str, file_type: str
) -> Dict[str, Any]:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    acl = credentials.default_acl
    expires_in = credentials.presigned_expiry

    presigned_data = s3_client.generate_presigned_post(
        credentials.bucket_name,
        file_path,
        Fields={"acl": acl, "Content-Type": file_type},
        Conditions=[
            {"acl": acl},
            {"Content-Type": file_type},
            # As an example, allow file size up to 10 MiB
            # More on conditions, here:
            # https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-HTTPPOSTConstructPolicy.html
            ["content-length-range", 1, credentials.max_size],
        ],
        ExpiresIn=expires_in,
    )

    return presigned_data


def create_presigned_url(object_name, bucket_name=None):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    credentials = s3_get_credentials()

    s3_client = boto3.client(
        config=Config(
            s3={"addressing_style": "path"}, signature_version="s3v4"
        ),
        service_name="s3",
        aws_access_key_id=credentials.access_key_id,
        aws_secret_access_key=credentials.secret_access_key,
        region_name=credentials.region_name,
    )

    credentials = s3_get_credentials()

    # Generate a presigned URL for the S3 object
    params = {"Bucket": credentials.bucket_name, "Key": object_name}
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=credentials.presigned_expiry,
        )
    except ClientError as e:
        logging.error(e)
        return None
    return response
