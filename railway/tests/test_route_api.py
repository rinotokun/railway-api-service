from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import Route
from railway.tests.fixtures import sample_station, sample_route

from railway.serializers import (
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer
)


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


ROUTE_URL = reverse("railway:routes-list")


def detail_url(route_id):
    return reverse("railway:routes-detail", args=[route_id])


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedRouteApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(ROUTE_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedRouteApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="user",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.route1 = sample_route()
        self.route2 = sample_route(
            source=sample_station(name="Odessa"),
            destination=sample_station(name="Cherkassy")
        )
        self.route3 = sample_route(
            source=sample_station(name="Kharkov"),
            destination=sample_station(name="Vinnytsia")
        )

    def test_get_route_list(self):
        result = self.client.get(ROUTE_URL)

        routes = Route.objects.all()
        serializer = RouteListSerializer(routes, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_retrieve_route_detail(self):
        url = detail_url(self.route1.id)
        result = self.client.get(url)

        serializer = RouteDetailSerializer(self.route1)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_create_route_forbidden(self):
        station_zaporizhzhia = sample_station(name="Zaporizhzhia")
        station_mykolaiv = sample_station(name="Mykolaiv")
        payload = {
            "source": station_zaporizhzhia.id,
            "destination": station_mykolaiv.id,
            "distance": 200
        }

        result = self.client.post(ROUTE_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class AdminRouteTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.route1 = sample_route()
        self.route2 = sample_route(
            source=sample_station(name="Odessa"),
            destination=sample_station(name="Cherkassy")
        )
        self.route3 = sample_route(
            source=sample_station(name="Kharkov"),
            destination=sample_station(name="Vinnytsia")
        )

    def test_create_route(self):
        station_zaporizhzhia = sample_station(name="Zaporizhzhia")
        station_mykolaiv = sample_station(name="Mykolaiv")
        payload = {
            "source": station_zaporizhzhia.id,
            "destination": station_mykolaiv.id,
            "distance": 200
        }

        result = self.client.post(ROUTE_URL, payload)

        route = Route.objects.get(id=result.data["id"])
        serializer = RouteSerializer(route, many=False)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        for key in payload:
            self.assertEqual(payload[key], serializer.data[key])

    def test_delete_route_not_allowed(self):
        url = detail_url(self.route1.id)

        result = self.client.delete(url)

        self.assertEqual(
            result.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
