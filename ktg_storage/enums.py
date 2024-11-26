from enum import Enum


class FileUploadStrategy(Enum):
    STANDARD = "standard"
    DIRECT = "direct"


class FileUploadStorage:
    LOCAL = "local"
    S3 = "s3"
