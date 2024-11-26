# Create your tests here.
from accounts.factories import UserFactory
from core.models import OBJECT_TYPE
from django.urls import reverse
from entity.factories import EntityFactory
from entity.models import Entity
from freezegun import freeze_time
from rest_framework import status
from rest_framework.response import Response
from testing.base import BaseAPITest

from .factories import AttachmentFactory
from .models import Storage


class StorageTest(BaseAPITest):
    def setUp(self):
        self.user = UserFactory()
        self.file = AttachmentFactory(uploaded_by=self.user)
        self.entity = EntityFactory(
            created_by=self.user, entity_type=Entity.ENTITY_TYPE.CONTRIBUTOR
        )

        self.list_file_url = reverse(
            "storage:list",
        )

        self.expired_files_url = reverse(
            "storage:expired-files",
        )

        self.update_file_url = reverse(
            "storage:update",
            kwargs={
                "pk": str(self.file.id),
            },
        )

        self.direct_upload_start_url = reverse("storage:direct_upload_start")
        self.direct_upload_finish_url = reverse("storage:direct_upload_finish")
        super().setUp()

    def test_unauthenticated_user_interracting_with_file(self):
        #  Given an ananymous user
        #  When I try to get my StorageFile
        res: Response = self.client.get(self.list_file_url)
        #  Then I should get a 401
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        payload = {
            "fileName": "string",
            "fileType": "string",
            "reminder": "2023-05-22T11:50:09.831Z",
            "expireAt": "2023-05-22T11:50:09.831Z",
            "object_type": OBJECT_TYPE.EMISSION_FACTOR,
        }

        # And When I try to create a new Resource
        res: Response = self.client.post(self.direct_upload_start_url, payload)
        # Then I should get a 401
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        #  Given an ananymous user
        #  When I try to update my StorageFile
        res: Response = self.client.patch(self.update_file_url)
        #  Then I should get a 401
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

        #  Given an anaonymous user
        #  When I try to delete my StorageFile
        res: Response = self.client.delete(self.update_file_url)
        #  Then I should get a 401
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_interracting_with_files(self):
        #  Given an authenticated user
        self.client.force_authenticate(user=self.user)
        #  When I try to get my StorageFile
        res: Response = self.client.get(self.list_file_url)
        #  Then I should get a 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # When I try to get my expired StorageFile
        res: Response = self.client.get(self.expired_files_url)
        # Then I should get a 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        payload = {
            "file_name": "string",
            "file_type": "string",
            "reminder": "2023-05-22T11:50:09.831Z",
            "expire_at": "2023-05-22T11:50:09.831Z",
            "object_type": OBJECT_TYPE.EMISSION_FACTOR,
        }

        # And When I try to create a new Resource
        res: Response = self.client.post(
            self.direct_upload_start_url,
            payload,
        )

        # Then I should get a 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["file"]["upload_finished_at"], None)

        #  When I try to mark file upload as finish
        fileId = res.data["file"]["id"]
        res: Response = self.client.post(
            self.direct_upload_finish_url, {"file_id": fileId}
        )
        #  Then I should get a 200
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotEqual(res.data["file"]["upload_finished_at"], None)

        #  And When I try to update my StorageFile
        old_file_name = self.file.file_name
        old_file_type = self.file.file_type
        new_expire_at = "2023-05-22T11:50:09Z"
        new_reminder = "2023-05-22T11:50:09Z"
        new_original_file_name = "new_original_file_name"
        res: Response = self.client.patch(
            self.update_file_url,
            {
                "file_name": "new_file_name",
                "file_type": "new_file_type",
                "original_file_name": new_original_file_name,
                "reminder": new_reminder,
                "expire_at": new_expire_at,
                "object_type": OBJECT_TYPE.EMISSION_FACTOR,
            },
        )
        #  Then I should get a 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        #  And the file name and type should not not change
        self.assertEqual(res.data["file_name"], old_file_name)
        self.assertEqual(res.data["file_type"], old_file_type)

        # And Should have the new original file name and reminder and expire_at
        self.assertEqual(
            res.data["original_file_name"], new_original_file_name
        )
        self.assertEqual(res.data["reminder"], new_reminder)
        self.assertEqual(res.data["expire_at"], new_expire_at)

        #  When I try to delete my StorageFile
        res: Response = self.client.delete(self.update_file_url)
        #  Then I should get a 204
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        # And When I try to get a File that not my File

        res: Response = self.client.get(self.update_file_url)
        # Then I should get a 404
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_upload_file_without_expiry_and_reminder(self):
        #  Given an authenticated user
        self.client.force_authenticate(user=self.user)
        #  When I try to get my StorageFile
        res: Response = self.client.get(self.list_file_url)
        #  Then I should get a 200
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        payload = {
            "file_name": "string",
            "file_type": "string",
            "object_type": OBJECT_TYPE.EMISSION_FACTOR,
        }

        # And When I try to create a new Resource
        res: Response = self.client.post(
            self.direct_upload_start_url,
            payload,
        )

        # Then I should get a 201
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["file"]["upload_finished_at"], None)


class FileModelTest(BaseAPITest):
    @freeze_time("2023-01-01")
    def test_get_files_that_need_to_remind_today(self):
        AttachmentFactory(reminder="2023-01-01T00:00:00Z")
        AttachmentFactory(reminder="2023-01-02T00:00:00Z")

        files = Storage.objects.get_files_that_need_to_remind_today()

        self.assertEqual(files.count(), 1)

    @freeze_time("2023-01-01")
    def test_get_files_that_expire_today(self):
        AttachmentFactory(expire_at="2023-01-01T00:00:00Z")
        AttachmentFactory(expire_at="2023-01-02T00:00:00Z")

        files = Storage.objects.get_files_that_expire_today()

        self.assertEqual(files.count(), 1)
