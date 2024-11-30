from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage


class StaticStorage(S3Boto3Storage):
    location = settings.STATIC_LOCATION


class PublicMediaStorage(S3Boto3Storage):
    location = settings.PUBLIC_MEDIA_LOCATION
    file_overwrite = False


class PrivateMediaStorage(S3Boto3Storage):
    location = settings.PRIVATE_MEDIA_LOCATION
    default_acl = "private"
    file_overwrite = False
    custom_domain = False


def get_public_storage_class():
    return PublicMediaStorage()


def get_private_storage_class():
    return PrivateMediaStorage()
