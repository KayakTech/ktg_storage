from ktg_storage.enums import FileUploadStorage
from ktg_storage.utils import file_generate_upload_path
from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model


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
    attachment = models.FileField(
        upload_to=file_generate_upload_path, blank=True, null=True
    )

    original_file_name = models.TextField()

    file_name = models.CharField(max_length=255, unique=True)
    file_type = models.CharField(max_length=255)
    uploaded_by = models.ForeignKey(
        get_user_model(), null=True, blank=True, on_delete=models.SET_NULL)
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
    def url(self):
        if settings.FILE_UPLOAD_STORAGE == FileUploadStorage.S3:
            return self.attachment.url

        return f"{settings.APP_DOMAIN}{self.attachment.url}"
