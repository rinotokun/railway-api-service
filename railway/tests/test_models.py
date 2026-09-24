from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from railway.models import image_file_path

from railway.tests.fixtures import (
    sample_station,
    sample_route,
    sample_train_type,
    sample_train,
    sample_crew,
    sample_journey,
    sample_order,
    sample_ticket
)


class ModelTest(TestCase):
    def setUp(self):
        self.station = sample_station()
        self.route = sample_route()
        self.train_type = sample_train_type()
        self.train = sample_train()
        self.crew = sample_crew()
        self.journey = sample_journey()
        self.user = get_user_model().objects.create_user(
            username="user", password="Password123"
        )
        self.order = sample_order(self.user)
        self.ticket = sample_ticket(order=self.order)

    def test_station_str(self):
        self.assertEqual(
            str(self.station),
            self.station.name
        )

    def test_route_str(self):
        self.assertEqual(
            str(self.route),
            f"{self.route.source} → {self.route.destination}"
        )

    def test_train_type_str(self):
        self.assertEqual(
            str(self.train_type),
            self.train_type.name
        )

    def test_train_str(self):
        self.assertEqual(
            str(self.train),
            self.train.name
        )

    def test_crew_str(self):
        self.assertEqual(
            str(self.crew),
            f"{self.crew.first_name} {self.crew.last_name}"
        )

    def test_crew_full_name(self):
        self.assertEqual(
            self.crew.full_name,
            f"{self.crew.first_name} {self.crew.last_name}"
        )

    def test_journey_str(self):
        self.assertEqual(
            str(self.journey),
            (
                f"{self.journey.route} | {str(self.journey.departure_time)} "
                f"— {str(self.journey.arrival_time)}"
            )
        )

    def test_order_str(self):
        self.assertEqual(
            str(self.order),
            str(self.order.created_at)
        )

    def test_ticket_str(self):
        self.assertEqual(
            str(self.ticket),
            (
                f"Route: {self.ticket.journey.route}\n"
                f"Cargo: {self.ticket.cargo} | Seat: {self.ticket.seat}\n"
                f"Departure time: {str(self.ticket.journey.departure_time)}\n"
                f"Arrival time: {str(self.ticket.journey.arrival_time)}"
            )
        )


class TicketValidationTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="user", password="Password123"
        )
        self.order = sample_order(self.user)

    def test_validation_error_when_cargo_out_of_range(self):
        with self.assertRaises(ValidationError) as context:
            sample_ticket(self.order, cargo=15)

        self.assertIn("cargo", context.exception.message_dict)

    def test_validation_error_when_seat_out_of_range(self):
        with self.assertRaises(ValidationError) as context:
            sample_ticket(self.order, seat=37)

        self.assertIn("seat", context.exception.message_dict)


class ImageFilePathTest(TestCase):
    def setUp(self):
        self.crew = sample_crew()
        self.train_type = sample_train_type()

    def test_correct_path_for_crew(self):
        path = image_file_path(self.crew, "photo.jpg")

        self.assertEqual(path.parts[0], "uploads")
        self.assertEqual(path.parts[1], "crew")

    def test_correct_path_for_train_type(self):
        path = image_file_path(self.train_type, "photo.jpg")

        self.assertEqual(path.parts[0], "uploads")
        self.assertEqual(path.parts[1], "traintype")

    def test_same_image_save_with_unique_name(self):
        image_1 = image_file_path(self.crew, "photo.jpg")
        image_2 = image_file_path(self.crew, "photo.jpg")

        self.assertNotEqual(image_1.parts[2], image_2.parts[2])
