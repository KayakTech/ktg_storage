from ktg_storage.auth_mixin import ApiAuthMixin
from ktg_storage.serializers import FileSerializer
from ktg_storage.serializers import FinishFileUploadSerializer
from ktg_storage.serializers import StartDirectFileUploadSerializer, CreatePresignedUrl
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.generics import CreateAPIView
from rest_framework.generics import ListAPIView
from rest_framework.generics import RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from .client import create_presigned_url
from .models import Storage
from .services import FileDirectUploadService


class FileDirectUploadStartApi(ApiAuthMixin, CreateAPIView):
    serializer_class = StartDirectFileUploadSerializer


class GetAllFileView(ApiAuthMixin, ListAPIView):
    serializer_class = FileSerializer

    def get_queryset(self):

        return Storage.objects.get_user_files(self.request.user)


class ExpiredFileListView(ApiAuthMixin, ListAPIView):
    serializer_class = FileSerializer

    def get_queryset(self):
        # Get the queryset of all files uploaded by the user
        user_documents = Storage.objects.get_user_files(self.request.user)
        # Filter the queryset to get the expired documents
        return user_documents.filter(expire_at__lte=timezone.now())


class FileDirectUploadFinishApi(ApiAuthMixin, CreateAPIView):
    serializer_class = FinishFileUploadSerializer

    def get_queryset(self):
        return Storage.objects.get_user_files(self.request.user)


class FileDirectUploadLocalApi(ApiAuthMixin, APIView):
    def post(self, request, file_id):
        file = get_object_or_404(Storage, id=file_id)

        file_obj = request.FILES["file"]

        service = FileDirectUploadService(request.user)
        file = service.upload_local(file=file, file_obj=file_obj)

        return Response({"id": file.id})


# update file view


class FileUpdateView(ApiAuthMixin, RetrieveUpdateDestroyAPIView):
    serializer_class = FileSerializer

    def get_queryset(self):
        return Storage.objects.get_user_files(self.request.user)

    def get_category(self):
        return

    def delete(self, request, *args, **kwargs):
        file = self.get_object()
        file.is_deleted = True
        file.save()
        return Response(
            {"message": "File deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )


class CreatePresignedUrl(ApiAuthMixin, CreateAPIView):
    serializer_class = CreatePresignedUrl

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_name = serializer.validated_data.get("file_name")

        return Response(
            data=create_presigned_url(object_name=file_name),
            status=status.HTTP_201_CREATED,
        )
