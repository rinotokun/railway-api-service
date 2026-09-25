from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import Order
from railway.tests.fixtures import (
    sample_journey,
    sample_route,
    sample_train,
    sample_station,
    sample_order,
    sample_ticket
)

from railway.serializers import (
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


ORDER_URL = reverse("railway:orders-list")


def detail_url(order_id):
    return reverse("railway:orders-detail", args=[order_id])


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedOrdersApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(ORDER_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedOrderApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = get_user_model().objects.create_user(
            username="user1",
            password="password"
        )
        self.user2 = get_user_model().objects.create_user(
            username="user2",
            password="password"
        )
        self.client.force_authenticate(self.user1)

        self.station_dnipro = sample_station(name="Dnipro")
        self.station_lviv = sample_station(name="Lviv")
        self.station_kyiv = sample_station(name="Kyiv")
        self.station_cherkassy = sample_station(name="Cherkassy")

        self.route_dnipro_lviv = sample_route(
            source=self.station_dnipro,
            destination=self.station_lviv
        )
        self.route_kyiv_cherkassy = sample_route(
            source=self.station_kyiv,
            destination=self.station_cherkassy
        )

        self.train_carpathians = sample_train(name="Carpathians-143")
        self.train_sloboda = sample_train(
            name="Sloboda-712",
            cargo_num=10,
            places_in_cargo=20
        )

        self.journey1 = sample_journey(
            route=self.route_dnipro_lviv,
            train=self.train_carpathians,
        )
        self.journey2 = sample_journey(
            route=self.route_kyiv_cherkassy,
            train=self.train_sloboda,
            departure_time=(timezone.now() + timedelta(days=1)),
            arrival_time=(timezone.now() + timedelta(days=2))
        )

        self.order1 = sample_order(self.user1)
        sample_ticket(self.order1, journey=self.journey1, cargo=1, seat=1)
        sample_ticket(self.order1, journey=self.journey1, cargo=1, seat=2)

        self.order2 = sample_order(self.user2)
        sample_ticket(self.order2, journey=self.journey2, cargo=1, seat=1)
        sample_ticket(self.order2, journey=self.journey2, cargo=1, seat=2)

    def test_user_see_only_own_orders(self):
        result = self.client.get(ORDER_URL)

        serializer_user1 = OrderListSerializer(self.order1)
        serializer_user2 = OrderListSerializer(self.order2)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_user1.data, result.data["results"])
        self.assertNotIn(serializer_user2.data, result.data["results"])

    def test_user_cant_get_not_own_order(self):
        url = detail_url(self.order2.id)
        result = self.client.get(url)

        self.assertEqual(result.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_can_create_order(self):
        payload = [
            {
                "cargo": 2,
                "seat": 1,
                "journey": self.journey1.id,
            },
            {
                "cargo": 2,
                "seat": 4,
                "journey": self.journey1.id,
            },
        ]

        result = self.client.post(
            ORDER_URL,
            {"tickets": payload},
            format="json"
        )

        order = Order.objects.get(id=result.data["id"])
        serializer = OrderSerializer(order)

        self.assertEqual(order.user, self.user1)
        self.assertEqual(result.status_code, status.HTTP_201_CREATED)

        for key in result.data:
            self.assertEqual(result.data[key], serializer.data[key])

    def test_cant_take_purchased_ticket(self):
        payload = [
            {
                "cargo": 1,
                "seat": 1,
                "journey": self.journey1.id,
            }
        ]
        order_before_invalid_post = Order.objects.all().count()

        result = self.client.post(
            ORDER_URL,
            {"tickets": payload},
            format="json"
        )
        order_after_invalid_post = Order.objects.all().count()

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(order_before_invalid_post, order_after_invalid_post)

    def test_cant_take_cargo_out_of_range(self):
        payload = [
            {
                "cargo": 15,
                "seat": 1,
                "journey": self.journey1.id,
            }
        ]

        result = self.client.post(
            ORDER_URL,
            {"tickets": payload},
            format="json"
        )

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cant_take_seat_out_of_range(self):
        payload = [
            {
                "cargo": 1,
                "seat": 100,
                "journey": self.journey1.id,
            }
        ]

        result = self.client.post(
            ORDER_URL,
            {"tickets": payload},
            format="json"
        )

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_order_detail(self):
        url = detail_url(self.order1.id)
        result = self.client.get(url)

        serializer = OrderDetailSerializer(self.order1)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_bad_request_when_tickets_empty(self):
        payload = []

        result = self.client.post(
            ORDER_URL,
            {"tickets": payload},
            format="json"
        )

        self.assertEqual(result.status_code, status.HTTP_400_BAD_REQUEST)
