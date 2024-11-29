# factories.py

import factory
from ktg_storage.models import Storage
from django.contrib.auth import get_user_model
from django.utils import timezone
import uuid


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    username = factory.Faker("user_name")
    email = factory.Faker("email")


class StorageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Storage

    id = factory.LazyFunction(uuid.uuid4)
    original_file_name = factory.Faker("file_name")
    file_name = factory.Faker("file_name")
    file_type = factory.Faker("mime_type")
    uploaded_by = factory.SubFactory(UserFactory)
    upload_finished_at = factory.LazyFunction(timezone.now)
    expire_at = factory.LazyFunction(timezone.now)
    reminder = factory.LazyFunction(timezone.now)
    attachment = factory.django.FileField(filename="test_file.txt")
