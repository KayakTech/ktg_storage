from ktg_storage.utils import file_generate_upload_path
from django.db import models
from django.utils import timezone
import uuid
from ktg_storage.client import s3_service
from typing import Optional
from django.conf import settings


class FileManger(models.Manager):
    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(is_deleted=False)
            .order_by("-created_at")
        )

    def get_user_files(self, user):

        return self.get_queryset().filter(
            uploaded_by=user, upload_finished_at__isnull=False
        )

    def get_files_that_expire_today(self):
        start_of_day = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date_of_day = timezone.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return self.get_queryset().filter(
            expire_at__range=[start_of_day, end_date_of_day]
        )

    def get_files_that_need_to_remind_today(
        self,
    ) -> models.QuerySet["Storage"]:
        start_of_day = timezone.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        end_date_of_day = timezone.now().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        return self.get_queryset().filter(
            reminder__range=[start_of_day, end_date_of_day]
        )


class Storage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    objects: FileManger = FileManger()
    file = models.FileField(
        upload_to=file_generate_upload_path, blank=True, null=True,
    )
    thumbnail = models.URLField(blank=True, null=True)

    original_file_name = models.TextField()

    file_name = models.CharField(max_length=255, unique=True)
    file_type = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,  null=True, blank=True, on_delete=models.SET_NULL)
    upload_finished_at = models.DateTimeField(blank=True, null=True)
    expire_at = models.DateTimeField(blank=True, null=True)
    reminder = models.DateTimeField(blank=True, null=True)

    @property
    def is_valid(self):
        """
        We consider a file "valid" if the the datetime flag has value.
        """
        return bool(self.upload_finished_at)

    @property
    def get_size(self) -> Optional[int]:
        return s3_service.get_file_size(self.file_name)

    @property
    def generate_presigned_url(self, expires: bool = True) -> Optional[str]:
        return s3_service.create_presigned_url(self.file_name, expires)

    def delete_file(self) -> bool:
        result = s3_service.delete_file(self.file_name)

        if result:
            self.file = None
            self.thumbnail = None
            self.save()

        return result

    @property
    def file_exists(self) -> bool:
        return s3_service.file_exists(self.file_name)

    @property
    def file_url(self):
        return s3_service.get_file_url(self.file_name)

    @property
    def file_path(self) -> str:
        return s3_service.get_file_path(self.file_name)
