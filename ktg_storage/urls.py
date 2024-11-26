from django.urls import path

from .views import ExpiredFileListView
from .views import FileDirectUploadFinishApi
from .views import FileDirectUploadLocalApi
from .views import FileDirectUploadStartApi
from .views import FileUpdateView
from .views import GetAllFileView
from .views import CreatePresignedUrl
app_name = "ktg_storage"

urlpatterns = [
    path(
        "upload/direct/start/",
        FileDirectUploadStartApi.as_view(),
        name="direct_upload_start",
    ),
    path(
        "upload/direct/finish/",
        FileDirectUploadFinishApi.as_view(),
        name="direct_upload_finish",
    ),
    path(
        "upload/direct/local/<str:file_id>/",
        FileDirectUploadLocalApi.as_view(),
        name="direct_local_upload",
    ),
    path("all/", GetAllFileView.as_view(), name="list"),
    path("files/<str:pk>/", FileUpdateView.as_view(), name="update"),
    path("expired-files/", ExpiredFileListView.as_view(), name="expired-files"),
    path("generate-presigned-url/", CreatePresignedUrl.as_view(),
         name="create_presigned_url"),
]
