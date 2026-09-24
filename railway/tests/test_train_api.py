from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import Train
from railway.serializers import TrainSerializer, TrainListSerializer
from railway.tests.fixtures import sample_train, sample_train_type


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


TRAIN_URL = reverse("railway:trains-list")


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedTrainApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(TRAIN_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedTrainApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="user",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.train1 = sample_train()
        self.train2 = sample_train(name="Black Sea-105")
        self.train3 = sample_train(name="EJ675-014")

    def test_get_train_list(self):
        result = self.client.get(TRAIN_URL)

        trains = Train.objects.all()
        serializer = TrainListSerializer(trains, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_create_train_forbidden(self):
        train_type = sample_train_type()
        payload = {
            "name": "HRCS2-001",
            "cargo_num": 9,
            "places_in_cargo": 58,
            "train_type": train_type.id
        }

        result = self.client.post(TRAIN_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class AdminTrainTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.train1 = sample_train()
        self.train2 = sample_train(name="Black Sea-105")
        self.train3 = sample_train(name="EJ675-014")

    def test_create_train(self):
        train_type = sample_train_type()
        payload = {
            "name": "HRCS2-001",
            "cargo_num": 9,
            "places_in_cargo": 58,
            "train_type": train_type.id
        }

        result = self.client.post(TRAIN_URL, payload)

        train = Train.objects.get(id=result.data["id"])
        serializer = TrainSerializer(train, many=False)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], serializer.data[key])

    def test_delete_train_not_allowed(self):
        url = TRAIN_URL + f"{self.train1.id}/"

        result = self.client.delete(url)

        self.assertEqual(
            result.status_code,
            status.HTTP_404_NOT_FOUND
        )
