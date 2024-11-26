from django.apps import AppConfig


class KTGStorageConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "ktg_storage"

    def ready(self) -> None:
        from ktg_storage.client import s3_get_credentials
        s3_get_credentials()
        return super().ready()
