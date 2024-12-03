from typing import Dict
from typing import Any
from typing import Optional
import logging
from dataclasses import dataclass
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from io import BytesIO


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


def get_s3_client():
    return boto3.client(
        service_name="s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
        config=Config(s3={"addressing_style": "path"},
                      signature_version="s3v4"),
    )


def get_s3_resource():
    return boto3.resource(
        service_name="s3",
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_S3_REGION_NAME,
    )


class S3Service:
    def __init__(self):
        self.client = get_s3_client()
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.acl = settings.AWS_DEFAULT_ACL
        self.expiry = settings.AWS_PRESIGNED_EXPIRY
        self.max_size = settings.FILE_MAX_SIZE

    def generate_presigned_post(
        self, *, file_path: str, file_type: str
    ) -> Dict[str, Any]:
        try:
            presigned_data = self.client.generate_presigned_post(
                self.bucket_name,
                file_path,
                Fields={"acl": self.acl, "Content-Type": file_type},
                Conditions=[
                    {"acl": self.acl},
                    {"Content-Type": file_type},
                    ["content-length-range", 1, self.max_size],
                ],
                ExpiresIn=self.expiry,
            )
            return presigned_data
        except ClientError as e:
            logging.error(f"Failed to generate presigned POST URL: {e}")
            raise

    def create_presigned_url(self, object_name: str, expires: bool = True) -> Optional[str]:

        expires_in = self.expiry if expires else 0

        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": object_name},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            logging.error(f"Failed to generate presigned URL: {e}")
            return None

    def get_file(
        self, object_name: str, download_path: Optional[str] = None
    ) -> Optional[bytes]:
        try:
            if download_path:
                self.client.download_file(
                    self.bucket_name, object_name, download_path)
                logging.info(f"File downloaded to {download_path}")
                return None
            else:
                obj = self.client.get_object(
                    Bucket=self.bucket_name, Key=object_name)
                return obj["Body"].read()
        except ClientError as e:
            logging.error(
                "Failed to retrieve file %s from S3: %s",
                object_name,
                e.response["Error"]["Message"],
            )

            return None

    def copy_file(self, source_object_name: str, destination_object_name: str) -> bool:

        copy_source = {"Bucket": self.bucket_name, "Key": source_object_name}
        try:
            self.client.copy(copy_source, self.bucket_name,
                             destination_object_name)
            logging.info("Copied %s to %s", source_object_name,
                         destination_object_name)

            return True
        except ClientError as e:
            logging.error(
                "Failed to copy file {} to {}: {}".format(
                    source_object_name, destination_object_name, e
                )
            )

            return False

    def delete_file(self, file_path: str) -> bool:
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError as e:
            logging.error(f"Failed to delete file from S3: {e}")
            return False

    def file_exists(self, key: str) -> bool:
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=key)
            return True
        except self.client.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False

            raise

    def get_file_size(self, key: str) -> int:
        if not self.file_exists(key):
            return 0

        try:
            response = self.client.head_object(
                Bucket=self.bucket_name, Key=key)

            return response["ContentLength"]
        except self.client.exceptions.ClientError:
            raise

    def get_file_path(self, object_name: str):
        if self.file_exists(object_name):
            return f"https://{self.bucket_name}.s3.amazonaws.com/{object_name}"
        return None

    def get_file_url(self, object_name: str) -> Optional[str]:
        try:
            return f"https://{self.bucket_name}.s3.amazonaws.com/{object_name}"
        except Exception as e:
            logging.error(f"Failed to generate URL for {object_name}: {e}")
            return None

    def get_file_content(self, object_name: str) -> Optional[bytes]:

        try:
            response = self.client.get_object(
                Bucket=self.bucket_name, Key=object_name)
            return response["Body"].read()
        except ClientError as e:
            logging.error(
                "Failed to fetch file %s: %s",
                object_name,
                e.response["Error"]["Message"],
            )

            return None

    def upload_file(self, file_path: str, object_name: str) -> bool:

        try:
            self.client.upload_file(file_path, self.bucket_name, object_name)
            logging.info(f"Uploaded {file_path} to {object_name}")
            return True
        except ClientError as e:
            message = f"Failed to upload {file_path} to {object_name}: {e}"
            logging.error(message)

            return False

    def upload_fileobj(
        self, fileobj: BytesIO, object_name: str, content_type: str, acl: Optional[str] = None
    ) -> bool:
        try:
            acl = acl or self.acl
            self.client.upload_fileobj(
                fileobj,
                self.bucket_name,
                object_name,
                ExtraArgs={"ContentType": content_type, "ACL": acl},
            )

            logging.info(f"Uploaded file-like object to {object_name}")
            return True
        except ClientError as e:
            logging.error(
                "Failed to upload file-like object to %s: %s",
                object_name,
                e.response["Error"]["Message"],
            )

            return False

    def get_file_metadata(self, object_name: str):
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name, Key=object_name)
            metadata = {
                "Size": response["ContentLength"],
                "LastModified": response["LastModified"],
                "ContentType": response["ContentType"],
                "ETag": response["ETag"],
            }
            return metadata
        except ClientError as e:
            logging.error(f"Failed to get metadata for {object_name}: {e}")
            return None


s3_service = S3Service()
