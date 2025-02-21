from ktg_storage.services import FileDirectUploadService
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from typing_extensions import TypedDict
from ktg_storage.client import s3_service

from ktg_storage.models import Storage


def User():
    from django.contrib.auth import get_user_model
    return get_user_model()


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User()

        exclude = ['groups', 'user_permissions', 'password']


class StorageValidatedData(TypedDict):
    file_name: str
    file_type: str
    upload_finished_at: str
    expire_at: str
    reminder: str


class FileSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer()
    file = serializers.SerializerMethodField()

    class Meta:
        model = Storage
        exclude = (
            "is_deleted",
        )
        read_only_fields = (
            "id",
            "upload_finished_at",
            "uploaded_by",
        )

    def update(self, instance: Storage, validated_data: dict):

        # Remove file_name and file_type from validated_data

        validated_data.pop("file_name", None)
        validated_data.pop("file_type", None)

        return super().update(instance, validated_data)

    def get_file(self, obj: Storage):
        if settings.IS_USING_LOCAL_STORAGE:
            return obj.file.url if obj.file else None

        return s3_service.create_presigned_url(obj.file.name)


class StartDirectFileUploadSerializer(serializers.Serializer):
    file = serializers.SerializerMethodField()
    presigned_data = serializers.DictField(read_only=True)

    file_name = serializers.CharField(write_only=True)
    file_type = serializers.CharField(write_only=True)
    reminder = serializers.DateTimeField(write_only=True, required=False)
    expire_at = serializers.DateTimeField(write_only=True, required=False)

    def create(self, validated_data: StorageValidatedData):

        user = self.context["request"].user
        if user.is_authenticated:
            validated_data["user"] = user
        service = FileDirectUploadService(user)
        data = service.start(validated_data)

        return data

    def get_file(self, obj: Storage):
        file = obj["file"]
        if file:
            return FileSerializer(file).data
        return


class FinishFileUploadSerializer(serializers.Serializer):
    file_id = serializers.CharField(write_only=True)
    file = serializers.SerializerMethodField()

    def create(self, validated_data):
        user = self.context["request"].user
        file_id = validated_data["file_id"]

        file = get_object_or_404(Storage, id=file_id)

        service = FileDirectUploadService(user)
        file = service.finish(file=file)
        return {"file": file, "file_id": file_id}

    def get_file(self, obj: Storage):
        file = obj["file"]
        if file:
            return FileSerializer(file).data
        return


class CreatePresignedUrl(serializers.Serializer):
    file_name = serializers.CharField()
    expires = serializers.BooleanField(default=True)
