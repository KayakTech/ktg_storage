# Register your models here.
from ktg_storage.models import Storage
from django.contrib import admin


@admin.register(Storage)
class AttachmentAdmin(admin.ModelAdmin):
    date_hierarchy = 'created_at'
    list_display = [
        "original_file_name",
        "file_name",
        "file_type",
        "upload_finished_at",
        "uploaded_by",
        "thumbnail"

    ]
    list_display_links = ['original_file_name', 'thumbnail', 'uploaded_by']
    list_filter = ['uploaded_by', 'file_type']
