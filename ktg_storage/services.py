import mimetypes
from typing import Any
from typing import Dict
from typing import Tuple
from PIL import Image

from django.contrib.auth import get_user_model
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone
from typing_extensions import TypedDict
from ktg_storage.client import s3_service
from moviepy.editor import VideoFileClip
import fitz
from ktg_storage.enums import FileUploadStorage
from ktg_storage.models import Storage
from ktg_storage.utils import bytes_to_mib
from ktg_storage.utils import file_generate_local_upload_url
from ktg_storage.utils import file_generate_name
from ktg_storage.utils import file_generate_upload_path
import magic
import io
import logging
import random
import tempfile
from io import BytesIO
from typing import Optional
User = get_user_model()


def _validate_file_size(file_obj):

    max_size = settings.FILE_MAX_SIZE

    if file_obj.size > max_size:
        message = "File is too large. It should not exceed {} MiB".format(
            bytes_to_mib(max_size))
        raise ValidationError(message)


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

        file.file = self.file_obj
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

        file: Storage = Storage(
            original_file_name=data["file_name"],
            file_name=file_generate_name(data["file_name"]),
            file_type=data["file_type"],
            uploaded_by=data.get("user", None),
            expire_at=data.get("expire_at"),
            reminder=data.get("reminder"),
            file=None,
        )

        file.full_clean()
        file.save()

        upload_path = file_generate_upload_path(file, file.file_name)

        """
        We are doing this in order to have an associated file for the field.
        """
        file.file = file.file.field.attr_class(
            file, file.file.field, upload_path
        )
        file.save()

        presigned_data: Dict[str, Any] = {}

        if (
            settings.FILE_UPLOAD_STORAGE == FileUploadStorage.S3
            or not settings.DEBUG
        ):
            presigned_data = s3_service.generate_presigned_post(
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
        file.file_name = file.file.name
        thumbnail = create_thumbnail(file.file.name)
        file.thumbnail = s3_service.get_file_path(thumbnail)

        file.save()

        return file

    @transaction.atomic
    def upload_local(self, *, file: Storage, file_obj) -> Storage:
        _validate_file_size(file_obj)

        # Potentially, check against user
        file.file = file_obj
        file.full_clean()
        file.save()

        return file


def create_thumbnail(
    s3_key: str, size: Tuple[int, int] = (128, 128)
) -> Optional[str]:
    try:

        if not s3_service.file_exists(s3_key):
            logging.error(f"File does not exist in S3: {s3_key}")
            return None

        image_data = s3_service.get_file_content(s3_key)
        if image_data is None:
            return None

        mime = magic.Magic(mime=True)
        mime_type = mime.from_buffer(image_data)

        if mime_type.startswith("image/"):
            return create_thumbnail_from_image(
                image_data, s3_key, mime_type, size
            )
        elif mime_type.startswith("video/"):
            return create_thumbnail_from_video(s3_key, size)
        elif mime_type == "application/pdf":
            return create_pdf_thumbnail(s3_key, size)
        else:
            logging.error(f"Unsupported MIME type: {mime_type}")
            return generate_random_thumbnail(size)

    except Exception as e:
        logging.error(f"Error creating thumbnail: {str(e)}", exc_info=True)
        return None


def create_thumbnail_from_image(
    image_data: bytes, s3_key: str, mime_type: str, size: Tuple[int, int]
):
    try:
        img = Image.open(BytesIO(image_data))

        if img.mode in ("RGBA", "LA") or (
            img.mode == "P" and "transparency" in img.info
        ):
            img = img.convert("RGB")
        img.thumbnail(size, Image.Resampling.LANCZOS)

        buffer = BytesIO()
        if mime_type == "image/jpeg":
            img.save(buffer, format="JPEG", quality=85, optimize=True)
        elif mime_type == "image/png":
            img.save(buffer, format="PNG", quality=85, optimize=True)
        elif mime_type == "image/gif":
            img.save(buffer, format="GIF", optimize=True)
        else:
            logging.error(f"Unsupported image MIME type: {mime_type}")
            return None

        buffer.seek(0)

        thumbnail_filename = "{}.jpg".format(
            s3_key.split("/")[-1].rsplit(".", 1)[0]
        )
        thumbnail_s3_path = f"thumbnails/{thumbnail_filename}"

        success = s3_service.upload_fileobj(
            buffer, thumbnail_s3_path, content_type="image/jpeg"
        )
        if not success:
            logging.error("Failed to upload thumbnail to S3.")
            return None

        return thumbnail_s3_path

    except Exception as e:
        message = f"Error creating image thumbnail: {str(e)}"
        logging.error(message, exc_info=True)

        return None


def create_thumbnail_from_video(s3_key: str, size: Tuple[int, int]):
    try:
        video_data = s3_service.get_file_content(s3_key)
        if video_data is None:
            return None

        with tempfile.NamedTemporaryFile(delete=True) as temp_video_file:
            temp_video_file.write(video_data)
            temp_video_file.flush()

            with VideoFileClip(temp_video_file.name) as clip:
                frame_time = clip.duration * 0.2
                frame = clip.get_frame(frame_time)

                img = Image.fromarray(frame)
                img.thumbnail(size, Image.Resampling.LANCZOS)

                buffer = BytesIO()
                img.save(buffer, format="JPEG", quality=85, optimize=True)
                buffer.seek(0)

                thumbnail_filename = "{}.jpg".format(
                    s3_key.split("/")[-1].rsplit(".", 1)[0]
                )
                thumbnail_s3_path = f"thumbnails/{thumbnail_filename}"

                success = s3_service.upload_fileobj(
                    buffer, thumbnail_s3_path, content_type="image/jpeg"
                )
                if not success:
                    logging.error("Failed to upload video thumbnail to S3.")
                    return None

                return thumbnail_s3_path

    except Exception as e:
        message = f"Error creating video thumbnail: {str(e)}"
        logging.error(message, exc_info=True)

        return None


def create_pdf_thumbnail(s3_key: str, size):
    file_content = s3_service.get_file_content(s3_key)
    if file_content is None:
        return

    try:
        pdf_file = fitz.open(stream=file_content, filetype="pdf")
        first_page = pdf_file.load_page(0)
        pix = first_page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((300, 300))

        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        thumbnail_filename = "{}.jpg".format(
            s3_key.split("/")[-1].rsplit(".", 1)[0]
        )
        thumbnail_s3_path = f"thumbnails/{thumbnail_filename}"

        success = s3_service.upload_fileobj(
            buffer, thumbnail_s3_path, content_type="image/png"
        )
        if not success:
            logging.error("Failed to upload PDF thumbnail to S3.")
            return None

        return thumbnail_s3_path

    except Exception as e:
        message = f"Error creating PDF thumbnail: {str(e)}"
        logging.error(message, exc_info=True)

        return None


def generate_random_thumbnail(self, size: Tuple[int, int]) -> str:
    img = Image.new("RGB", size, color=self.random_color())

    buffer = BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    buffer.seek(0)

    thumbnail_filename = f"{random.randint(1000, 9999)}.jpg"
    thumbnail_s3_path = f"thumbnails/{thumbnail_filename}"

    success = s3_service.upload_fileobj(
        buffer, thumbnail_s3_path, content_type="image/jpeg"
    )
    if not success:
        logging.error("Failed to upload random thumbnail to S3.")
        return None

    return thumbnail_s3_path


def random_color(self) -> Tuple[int, int, int]:
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)
