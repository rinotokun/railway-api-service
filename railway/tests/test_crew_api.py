import tempfile
import os
import shutil

from PIL import Image
from django.contrib.auth import get_user_model
from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import Crew
from railway.serializers import CrewSerializer
from railway.tests.fixtures import sample_crew


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


CREW_URL = reverse("railway:crews-list")


def image_upload_url(crew_id):
    return reverse("railway:crews-upload-image", args=[crew_id])


@override_settings(
    MEDIA_ROOT=tempfile.mkdtemp(),
    CACHES=DUMMY_CACHE
)
class CrewImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.crew = sample_crew()

    def tearDown(self):
        self.crew.image.delete()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def test_upload_image_to_crew(self):
        url = image_upload_url(self.crew.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {"image": ntf},
                format="multipart"
            )
        self.crew.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.crew.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.crew.id)
        res = self.client.post(
            url,
            {"image": "not image"},
            format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_url_is_shown_on_crew_list(self):
        url = image_upload_url(self.crew.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(CREW_URL)

        self.assertIsNotNone(res.data[0]["image"])


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedCrewApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(CREW_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedCrewApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="user",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.crew1 = sample_crew()
        self.crew2 = sample_crew(first_name="Victoria")
        self.crew3 = sample_crew(first_name="Olga")

    def test_get_crew_list(self):
        result = self.client.get(CREW_URL)

        crews = Crew.objects.all()
        serializer = CrewSerializer(crews, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_create_crew_forbidden(self):
        payload = {
            "first_name": "Nikolai",
            "last_name": "Zinkov"
        }

        result = self.client.post(CREW_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class AdminCrewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.crew1 = sample_crew()
        self.crew2 = sample_crew(first_name="Victoria")
        self.crew3 = sample_crew(first_name="Olga")

    def test_create_crew(self):
        payload = {
            "first_name": "Nikolai",
            "last_name": "Zinkov"
        }

        result = self.client.post(CREW_URL, payload)

        crew = Crew.objects.get(id=result.data["id"])

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(crew, key))

    def test_delete_crew_not_allowed(self):
        url = CREW_URL + f"{self.crew1.id}/"

        result = self.client.delete(url)

        self.assertEqual(
            result.status_code,
            status.HTTP_404_NOT_FOUND
        )
