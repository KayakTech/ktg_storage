import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from io import BytesIO
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def assert_settings(required_settings, error_message_prefix=""):

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

            "STATIC_LOCATION",
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
            ["content-length-range", 1, credentials.max_size],
        ],
        ExpiresIn=expires_in,
    )

    return presigned_data


def create_presigned_url(object_name, bucket_name=None):
    """Generate a presigned URL to share an S3 object

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

    # Generate a presigned URL for the S3 object
    params = {"Bucket": credentials.bucket_name, "Key": object_name}
    try:
        response = s3_client.generate_presigned_url(
            "get_object",
            Params=params,
            ExpiresIn=credentials.presigned_expiry,
        )
    except ClientError as e:
        logging.error(f"Error generating presigned URL: {e}")
        return None
    return response


def upload_file(file_path: str, object_name: str) -> bool:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        s3_client.upload_file(file_path, credentials.bucket_name, object_name)
        logging.info(f"Uploaded {file_path} to {object_name}")
        return True
    except ClientError as e:
        logging.error(f"Failed to upload {file_path} to {object_name}: {e}")
        return False


def get_file(object_name: str, download_path: Optional[str] = None) -> Optional[bytes]:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        if download_path:
            s3_client.download_file(
                credentials.bucket_name, object_name, download_path)
            logging.info(f"File downloaded to {download_path}")
            return None
        else:
            obj = s3_client.get_object(
                Bucket=credentials.bucket_name, Key=object_name)
            return obj["Body"].read()
    except ClientError as e:
        logging.error(f"Failed to retrieve file {object_name} from S3: {e}")
        return None


def copy_file(source_object_name: str, destination_object_name: str) -> bool:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    copy_source = {"Bucket": credentials.bucket_name,
                   "Key": source_object_name}
    try:
        s3_client.copy(copy_source, credentials.bucket_name,
                       destination_object_name)
        logging.info(f"Copied {source_object_name} to {
                     destination_object_name}")
        return True
    except ClientError as e:
        logging.error(f"Failed to copy file {source_object_name} to {
                      destination_object_name}: {e}")
        return False


def delete_file(file_path: str) -> bool:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        s3_client.delete_object(Bucket=credentials.bucket_name, Key=file_path)
        logging.info(f"Deleted {file_path} from S3")
        return True
    except ClientError as e:
        logging.error(f"Failed to delete file from S3: {e}")
        return False


def file_exists(key: str) -> bool:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        s3_client.head_object(Bucket=credentials.bucket_name, Key=key)
        return True
    except ClientError as e:
        if e.response["Error"]["Code"] == "404":
            return False
        raise


def get_file_size(key: str) -> int:
    if not file_exists(key):
        return 0

    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        response = s3_client.head_object(
            Bucket=credentials.bucket_name, Key=key)
        return response["ContentLength"]
    except ClientError as e:
        logging.error(f"Error fetching file size for {key}: {e}")
        raise


def get_file_path(object_name: str) -> Optional[str]:
    credentials = s3_get_credentials()

    if file_exists(object_name):
        return f"https://{credentials.bucket_name}.s3.amazonaws.com/{object_name}"
    return None


def get_file_content(object_name: str) -> Optional[bytes]:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        response = s3_client.get_object(
            Bucket=credentials.bucket_name, Key=object_name)
        return response["Body"].read()
    except ClientError as e:
        logging.error(f"Failed to fetch file {object_name} from S3: {e}")
        return None


def upload_fileobj(fileobj: BytesIO, object_name: str, content_type: str) -> bool:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    try:
        s3_client.upload_fileobj(
            fileobj,
            credentials.bucket_name,
            object_name,
            ExtraArgs={"ContentType": content_type,
                       "ACL": credentials.default_acl},
        )

        logging.info(f"Uploaded file-like object to {object_name}")
        return True
    except ClientError as e:
        logging.error(
            f"Failed to upload file-like object to {object_name}: {e}")
        return False


def generate_url(object_name: str, has_expire: bool = True) -> str:
    credentials = s3_get_credentials()
    s3_client = s3_get_client()

    if has_expire:
        try:
            url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': credentials.bucket_name,
                    'Key': object_name
                },
                ExpiresIn=credentials.presigned_expiry)

            return url
        except ClientError as e:
            logging.error(f"Error generating presigned URL: {e}")
            return None
    else:
        # If has_expire is False, generate a public URL (no expiration)
        public_url = f"https://{credentials.bucket_name}.s3.amazonaws.com/{object_name}"
        return public_url
