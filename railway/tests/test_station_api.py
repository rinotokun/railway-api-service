from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import Station
from railway.serializers import StationSerializer
from railway.tests.fixtures import sample_station


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


STATION_URL = reverse("railway:stations-list")


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedStationApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(STATION_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedStationApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="user",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.station1 = sample_station()
        self.station2 = sample_station(name="Kharkov")
        self.station3 = sample_station(name="Lviv")

    def test_get_station_list(self):
        result = self.client.get(STATION_URL)

        stations = Station.objects.all()
        serializer = StationSerializer(stations, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_create_station_forbidden(self):
        payload = {
            "name": "Odessa",
            "latitude": Decimal("25.12"),
            "longitude": Decimal("30.22")
        }

        result = self.client.post(STATION_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class AdminStationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.station1 = sample_station()
        self.station2 = sample_station(name="Kharkov")
        self.station3 = sample_station(name="Lviv")

    def test_create_station(self):
        payload = {
            "name": "Odessa",
            "latitude": Decimal("25.12"),
            "longitude": Decimal("30.22")
        }

        result = self.client.post(STATION_URL, payload)

        station = Station.objects.get(id=result.data["id"])

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], getattr(station, key))

    def test_delete_station_not_allowed(self):
        url = STATION_URL + f"{self.station1.id}/"

        result = self.client.delete(url)

        self.assertEqual(
            result.status_code,
            status.HTTP_404_NOT_FOUND
        )
