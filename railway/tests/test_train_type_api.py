import tempfile
import os
import shutil

from PIL import Image
from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import TrainType
from railway.serializers import TrainTypeSerializer
from railway.tests.fixtures import sample_train_type, sample_train
from railway_service.settings import BASE_DIR


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


TRAIN_TYPE_URL = reverse("railway:train-types-list")


def image_upload_url(train_type_id):
    return reverse("railway:train-types-upload-image", args=[train_type_id])


@override_settings(
    MEDIA_ROOT=BASE_DIR / "test_image_train_type",
    CACHES=DUMMY_CACHE
)
class TrainTypeImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_superuser(
            username="admin",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.train_type = sample_train_type()
        self.train = sample_train(train_type=self.train_type)

    def tearDown(self):
        self.train_type.image.delete()

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree("./test_image_train_type", ignore_errors=True)
        super().tearDownClass()

    def test_upload_image_to_train_type(self):
        url = image_upload_url(self.train_type.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = self.client.post(
                url,
                {"image": ntf},
                format="multipart"
            )
        self.train_type.refresh_from_db()

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.train_type.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.train_type.id)
        res = self.client.post(
            url,
            {"image": "not image"},
            format="multipart"
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_url_is_shown_on_train_type_list(self):
        url = image_upload_url(self.train_type.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(TRAIN_TYPE_URL)

        self.assertIsNotNone(res.data[0]["image"])

    def test_image_url_is_shown_on_train_list(self):
        url = image_upload_url(self.train_type.id)
        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            self.client.post(url, {"image": ntf}, format="multipart")
        res = self.client.get(reverse("railway:trains-list"))

        self.assertIsNotNone(res.data[0]["train_image"])

    def test_not_admin_cant_upload_image(self):
        url = image_upload_url(self.train_type.id)
        client = APIClient()
        regular_user = get_user_model().objects.create_user(
            username="user",
            password="SuperPas"
        )
        client.force_authenticate(regular_user)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as ntf:
            img = Image.new("RGB", (10, 10))
            img.save(ntf, format="JPEG")
            ntf.seek(0)
            res = client.post(url, {"image": ntf}, format="multipart")

        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedTrainTypeApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(TRAIN_TYPE_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedTrainTypeApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="user",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.train_type1 = sample_train_type()
        self.train_type2 = sample_train_type(name="Night Express")
        self.train_type3 = sample_train_type(name="Suburban")

    def test_get_train_type_list(self):
        result = self.client.get(TRAIN_TYPE_URL)

        train_types = TrainType.objects.all()
        serializer = TrainTypeSerializer(train_types, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_create_train_type_forbidden(self):
        payload = {
            "name": "Black"
        }

        result = self.client.post(TRAIN_TYPE_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class AdminTrainTypeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.train_type1 = sample_train_type()
        self.train_type2 = sample_train_type(name="Night Express")
        self.train_type3 = sample_train_type(name="Suburban")

    def test_create_train_type(self):
        payload = {
            "name": "Fastest"
        }

        result = self.client.post(TRAIN_TYPE_URL, payload)

        train_type = TrainType.objects.get(id=result.data["id"])

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(train_type, key))

    def test_delete_train_type_not_allowed(self):
        url = TRAIN_TYPE_URL + f"{self.train_type1.id}/"

        result = self.client.delete(url)

        self.assertEqual(
            result.status_code,
            status.HTTP_404_NOT_FOUND
        )
