from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient
from rest_framework import status

from railway.models import Journey
from railway.tests.fixtures import (
    sample_journey,
    sample_route,
    sample_train,
    sample_crew,
    sample_station,
    sample_order,
    sample_ticket
)

from railway.serializers import (
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer
)


DUMMY_CACHE = {
    "default": {
        "BACKEND": "django.core.cache.backends.dummy.DummyCache"
    }
}


JOURNEY_URL = reverse("railway:journeys-list")


def detail_url(journey_id):
    return reverse("railway:journeys-detail", args=[journey_id])


@override_settings(CACHES=DUMMY_CACHE)
class UnauthenticatedJourneyApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        result = self.client.get(JOURNEY_URL)

        self.assertEqual(result.status_code, status.HTTP_401_UNAUTHORIZED)


@override_settings(CACHES=DUMMY_CACHE)
class AuthenticatedJourneyApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="user",
            password="password"
        )
        self.client.force_authenticate(self.user)

        self.station_dnipro = sample_station(name="Dnipro")
        self.station_lviv = sample_station(name="Lviv")
        self.station_kyiv = sample_station(name="Kyiv")
        self.station_cherkassy = sample_station(name="Cherkassy")
        self.station_vinnytsia = sample_station(name="Vinnytsia")
        self.station_odessa = sample_station(name="Odessa")

        self.route_dnipro_lviv = sample_route(
            source=self.station_dnipro,
            destination=self.station_lviv
        )
        self.route_kyiv_cherkassy = sample_route(
            source=self.station_kyiv,
            destination=self.station_cherkassy
        )
        self.route_vinnytsia_odessa = sample_route(
            source=self.station_vinnytsia,
            destination=self.station_odessa
        )

        self.train_carpathians = sample_train(name="Carpathians-143")
        self.train_sloboda = sample_train(
            name="Sloboda-712",
            cargo_num=10,
            places_in_cargo=20
        )
        self.train_capital = sample_train(
            name="Capital-091",
            cargo_num=30,
            places_in_cargo=50
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
        self.journey3 = sample_journey(
            route=self.route_vinnytsia_odessa,
            train=self.train_capital,
            departure_time=(timezone.now() + timedelta(days=3)),
            arrival_time=(timezone.now() + timedelta(days=4))
        )

    def test_get_journey_list(self):
        result = self.client.get(JOURNEY_URL)

        for journey in result.data:
            del journey["tickets_available"]

        journeys = Journey.objects.all()
        serializer = JourneyListSerializer(journeys, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_retrieve_journey_detail(self):
        url = detail_url(self.journey1.id)
        result = self.client.get(url)

        serializer = JourneyDetailSerializer(self.journey1)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)

    def test_filter_journey_by_departure_date(self):
        departure_date = timezone.localdate()
        result = self.client.get(
            JOURNEY_URL,
            {"departure_date": departure_date}
        )

        for journey in result.data:
            del journey["tickets_available"]

        journeys = Journey.objects.filter(departure_time__date=departure_date)
        serializer = JourneyListSerializer(journeys, many=True)

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertEqual(result.data, serializer.data)
        self.assertEqual(len(result.data), len(serializer.data))

    def test_filter_journey_by_source(self):
        result = self.client.get(
            JOURNEY_URL,
            {"source": "Dnipro"}
        )

        for journey in result.data:
            del journey["tickets_available"]

        serializer_journey_source_dnipro = JourneyListSerializer(self.journey1)
        serializer_journey_source_kyiv = JourneyListSerializer(self.journey2)
        serializer_journey_source_vinnytsia = JourneyListSerializer(
            self.journey3
        )

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_journey_source_dnipro.data, result.data)
        self.assertNotIn(serializer_journey_source_kyiv.data, result.data)
        self.assertNotIn(serializer_journey_source_vinnytsia.data, result.data)

    def test_filter_journey_by_destination(self):
        result = self.client.get(
            JOURNEY_URL,
            {"destination": "Odessa"}
        )

        for journey in result.data:
            del journey["tickets_available"]

        serializer_journey_destination_lviv = JourneyListSerializer(
            self.journey1
        )
        serializer_journey_destination_cherkassy = JourneyListSerializer(
            self.journey2
        )
        serializer_journey_destination_odessa = JourneyListSerializer(
            self.journey3
        )

        self.assertEqual(result.status_code, status.HTTP_200_OK)
        self.assertIn(serializer_journey_destination_odessa.data, result.data)
        self.assertNotIn(serializer_journey_destination_lviv.data, result.data)
        self.assertNotIn(
            serializer_journey_destination_cherkassy.data,
            result.data
        )

    def test_correct_tickets_available_num(self):
        order = sample_order(self.user)
        sample_ticket(order, journey=self.journey1, cargo=1, seat=1)
        sample_ticket(order, journey=self.journey1, cargo=1, seat=2)
        sample_ticket(order, journey=self.journey2, cargo=1, seat=1)

        result = self.client.get(JOURNEY_URL)
        tickets_available = [
            journey["tickets_available"]
            for journey in result.data
        ]

        expected = [
            (
                self.train_carpathians.cargo_num
                * self.train_carpathians.places_in_cargo
                - 2
            ),
            (
                self.train_sloboda.cargo_num
                * self.train_sloboda.places_in_cargo
                - 1
            ),
            (
                self.train_capital.cargo_num
                * self.train_capital.places_in_cargo
            )
        ]

        self.assertEqual(tickets_available, expected)

    def test_create_journey_forbidden(self):
        crew1 = sample_crew()
        crew2 = sample_crew(first_name="Olga")
        payload = {
            "route": self.route_dnipro_lviv.id,
            "train": self.train_carpathians.id,
            "crew": [crew1.id, crew2.id],
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(days=1)
        }

        result = self.client.post(JOURNEY_URL, payload)

        self.assertEqual(result.status_code, status.HTTP_403_FORBIDDEN)


@override_settings(CACHES=DUMMY_CACHE)
class AdminJourneyTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="admin",
            password="password",
            is_staff=True
        )
        self.client.force_authenticate(self.user)

        self.journey = sample_journey()

    def test_create_journey(self):
        route = sample_route()
        train = sample_train()
        crew1 = sample_crew()
        crew2 = sample_crew(first_name="Olga")
        payload = {
            "route": route.id,
            "train": train.id,
            "crew": [crew1.id, crew2.id],
            "departure_time": timezone.now(),
            "arrival_time": timezone.now() + timedelta(days=1)
        }

        result = self.client.post(JOURNEY_URL, payload)

        journey = Journey.objects.get(id=result.data["id"])
        serializer = JourneySerializer(journey, many=False)

        self.assertEqual(result.status_code, status.HTTP_201_CREATED)
        self.assertEqual(payload["departure_time"], journey.departure_time)
        self.assertEqual(payload["arrival_time"], journey.arrival_time)

        for key in ("departure_time", "arrival_time"):
            del payload[key]
            del serializer.data[key]

        for key in payload:
            self.assertEqual(payload[key], serializer.data[key])

    def test_delete_journey_not_allowed(self):
        url = detail_url(self.journey.id)

        result = self.client.delete(url)

        self.assertEqual(
            result.status_code,
            status.HTTP_405_METHOD_NOT_ALLOWED
        )
