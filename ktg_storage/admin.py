# Register your models here.
from ktg_storage.models import Storage
from django.contrib import admin


@admin.register(Storage)
class AttachmentAdmin(admin.ModelAdmin):
    list_display = [
        "original_file_name",
        "file_name",
        "file_type",
        "upload_finished_at",
        "uploaded_by",

    ]
