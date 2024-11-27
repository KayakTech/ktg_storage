from django.urls import path
from ktg_storage import views
app_name = "ktg_storage"

urlpatterns = [
    path(
        "upload/direct/start/",
        views.FileDirectUploadStartApi.as_view(),
        name="direct_upload_start",
    ),
    path(
        "upload/direct/finish/",
        views.FileDirectUploadFinishApi.as_view(),
        name="direct_upload_finish",
    ),
    path(
        "upload/direct/local/<str:file_id>/",
        views.FileDirectUploadLocalApi.as_view(),
        name="direct_local_upload",
    ),
    path("all/", views.GetAllFileView.as_view(), name="list"),
    path("files/<str:pk>/", views.FileUpdateView.as_view(), name="update"),
    path("expired-files/", views.ExpiredFileListView.as_view(), name="expired-files"),
    path("generate-presigned-url/", views.CreatePresignedUrl.as_view(),
         name="create_presigned_url"),
]
