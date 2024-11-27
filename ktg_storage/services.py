import mimetypes
from typing import Any
from typing import Dict
from typing import Tuple

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from typing_extensions import TypedDict
from ktg_storage.client import s3_generate_presigned_post

from ktg_storage.enums import FileUploadStorage
from ktg_storage.models import Storage
from ktg_storage.utils import bytes_to_mib
from ktg_storage.utils import file_generate_local_upload_url
from ktg_storage.utils import file_generate_name
from ktg_storage.utils import file_generate_upload_path
User = get_user_model()


def _validate_file_size(file_obj):

    max_size = settings.FILE_MAX_SIZE

    if file_obj.size > max_size:
        # message = "File is too large. It
        # should not exceed {} MiB".format(
        # bytes_to_mib(max_size))
        raise ValidationError('file too big')


class FileStandardUploadService:
    """
    This also serves as an example of a service class,
    which encapsulates 2 different behaviors (create & update) under a namespace.

    Meaning, we use the class here for:

    1. The namespace
    2. The ability to reuse `_infer_file_name_and_type` (which can also be an util)
    """

    def __init__(self, user, file_obj):
        self.user = user
        self.file_obj = file_obj

    def _infer_file_name_and_type(
        self, file_name: str = "", file_type: str = ""
    ) -> Tuple[str, str]:
        if not file_name:
            file_name = self.file_obj.name

        if not file_type:
            guessed_file_type, encoding = mimetypes.guess_type(file_name)

            if guessed_file_type is None:
                file_type = ""
            else:
                file_type = guessed_file_type

        return file_name, file_type

    @transaction.atomic
    def create(
        self,
        object_type: str,
        file_name: str = "",
        file_type: str = "",
    ) -> Storage:
        _validate_file_size(self.file_obj)

        file_name, file_type = self._infer_file_name_and_type(
            file_name, file_type
        )

        obj = Storage(
            file=self.file_obj,
            object_type=object_type,
            original_file_name=file_name,
            file_name=file_generate_name(file_name),
            file_type=file_type,
            uploaded_by=self.user,
            upload_finished_at=timezone.now(),
        )

        obj.full_clean()
        obj.save()

        return obj

    @transaction.atomic
    def update(
        self, file: Storage, file_name: str = "", file_type: str = ""
    ) -> Storage:
        _validate_file_size(self.file_obj)

        file_name, file_type = self._infer_file_name_and_type(
            file_name, file_type
        )

        file.attachment = self.file_obj
        file.original_file_name = file_name
        file.file_name = file_generate_name(file_name)
        file.file_type = file_type
        file.uploaded_by = self.user
        file.upload_finished_at = timezone.now()

        file.full_clean()
        file.save()

        return file


class StartFileUploadData(TypedDict):
    file: Storage
    presigned_data: Dict[str, Any]


class FileDirectUploadService:

    class StorageValidatedData(TypedDict):
        file_name: str
        file_type: str
        upload_finished_at: str
        expire_at: str
        reminder: str
        user: str
        object_type: str

    def __init__(self, user):
        self.user = user

    @transaction.atomic
    def start(self, data: StorageValidatedData) -> StartFileUploadData:

        file = Storage(
            original_file_name=data["file_name"],
            file_name=file_generate_name(data["file_name"]),
            file_type=data["file_type"],
            uploaded_by=data.get("user", None),
            expire_at=data.get("expire_at"),
            reminder=data.get("reminder"),
            attachment=None,
        )

        file.full_clean()
        file.save()

        upload_path = file_generate_upload_path(file, file.file_name)

        """
        We are doing this in order to have an associated file for the field.
        """
        file.attachment = file.attachment.field.attr_class(
            file, file.attachment.field, upload_path
        )
        file.save()

        presigned_data: Dict[str, Any] = {}

        if (
            settings.FILE_UPLOAD_STORAGE == FileUploadStorage.S3
            or not settings.DEBUG
        ):
            presigned_data = s3_generate_presigned_post(
                file_path=upload_path, file_type=file.file_type
            )

        else:
            presigned_data = {
                "url": file_generate_local_upload_url(file_id=str(file.id)),
            }

        return {
            "file": file,
            "presigned_data": presigned_data,
        }

    @transaction.atomic
    def finish(self, *, file: Storage) -> Storage:
        # Potentially, check against user
        file.upload_finished_at = timezone.now()
        file.full_clean()
        file.save()

        return file

    @transaction.atomic
    def upload_local(self, *, file: Storage, file_obj) -> Storage:
        _validate_file_size(file_obj)

        # Potentially, check against user
        file.attachment = file_obj
        file.full_clean()
        file.save()

        return file
