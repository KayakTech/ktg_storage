# Generated by Django 5.1.3 on 2024-11-30 11:41

import django.db.models.deletion
import ktg_storage.storage_backends
import ktg_storage.utils
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Storage',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('is_deleted', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('attachment', models.FileField(blank=True, null=True, storage=ktg_storage.storage_backends.get_private_storage_class, upload_to=ktg_storage.utils.file_generate_upload_path)),
                ('original_file_name', models.TextField()),
                ('file_name', models.CharField(max_length=255, unique=True)),
                ('file_type', models.CharField(max_length=255)),
                ('upload_finished_at', models.DateTimeField(blank=True, null=True)),
                ('expire_at', models.DateTimeField(blank=True, null=True)),
                ('reminder', models.DateTimeField(blank=True, null=True)),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
