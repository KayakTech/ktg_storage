
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from ktg_storage.models import Storage
from ktg_storage.factories import StorageFactory, UserFactory
from django.urls import reverse
from django.utils import timezone


class StorageApiTests(TestCase):
    def setUp(self):
        self.user = UserFactory.create()
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.file1 = StorageFactory.create(uploaded_by=self.user)
        self.file2 = StorageFactory.create(
            uploaded_by=self.user, expire_at=timezone.now() - timezone.timedelta(days=1))

    def test_get_all_files(self):
        url = reverse('ktg_storage:list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        files = response.json()

        self.assertEqual(len(files), 2)

        self.assertEqual(str(files[0]["uploaded_by"][0]["id"]), str(
            self.user.id))
        self.assertEqual(str(files[1]["uploaded_by"][0]["id"]), str(
            self.user.id))

    def test_get_expired_files(self):
        url = reverse('ktg_storage:expired-files')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        files = response.json()
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0]["id"], str(self.file2.id))

    def test_file_update(self):
        url = reverse('ktg_storage:update', kwargs={'pk': self.file1.id})
        new_data = {
            "expire_at": timezone.now() + timezone.timedelta(days=2)
        }

        response = self.client.patch(url, new_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_file = Storage.objects.get(id=self.file1.id)
        self.assertEqual(updated_file.expire_at.date(),
                         (timezone.now() + timezone.timedelta(days=2)).date())

    def test_delete_file(self):
        url = reverse('ktg_storage:update', kwargs={'pk': self.file1.id})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_file_presigned_url(self):
        url = reverse('ktg_storage:create_presigned_url')
        data = {
            "file_name": "test_file.txt"
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_start_file_upload(self):
        url = reverse('ktg_storage:direct_upload_start')
        data = {
            "file_name": "test_file_to_upload.txt",
            "file_type": "text/plain",
            "reminder": timezone.now(),
            "expire_at": timezone.now() + timezone.timedelta(days=5),
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        self.assertIn("file", response.json())
        self.assertIn("presigned_data", response.json())

    def test_finish_file_upload(self):
        url = reverse('ktg_storage:direct_upload_finish')
        data = {
            "file_id": str(self.file1.id)
        }

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        file = Storage.objects.get(id=self.file1.id)
        self.assertIsNotNone(file.upload_finished_at)
