import pathlib
import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils.text import slugify


def image_file_path(instance, filename):
    filename = (
        f"{slugify(str(instance))}"
        f"-{uuid.uuid4()}"
        + pathlib.Path(filename).suffix
    )
    class_name = instance.__class__.__name__.lower()

    return pathlib.Path(f"uploads/{class_name}/") / pathlib.Path(filename)


class Station(models.Model):
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=8, decimal_places=2)
    longitude = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Route(models.Model):
    source = models.ForeignKey(
        Station,
        related_name="route_sources",
        on_delete=models.CASCADE
    )
    destination = models.ForeignKey(
        Station,
        related_name="route_destinations",
        on_delete=models.CASCADE
    )
    distance = models.IntegerField()

    class Meta:
        ordering = ["distance"]

    def __str__(self):
        return self.source.name + " → " + self.destination.name


class TrainType(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to=image_file_path,
        null=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Train(models.Model):
    name = models.CharField(max_length=255)
    cargo_num = models.IntegerField()
    places_in_cargo = models.IntegerField()
    train_type = models.ForeignKey(
        TrainType,
        related_name="trains",
        on_delete=models.PROTECT,
        null=True
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Crew(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    image = models.ImageField(
        upload_to=image_file_path,
        null=True
    )

    class Meta:
        ordering = ["first_name"]
        verbose_name = "Crew member"
        verbose_name_plural = "Crews"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Journey(models.Model):
    route = models.ForeignKey(
        Route,
        related_name="journeys",
        on_delete=models.CASCADE
    )
    train = models.ForeignKey(
        Train,
        related_name="journeys",
        on_delete=models.PROTECT
    )
    crew = models.ManyToManyField(Crew, related_name="journeys", blank=True)
    departure_time = models.DateTimeField()
    arrival_time = models.DateTimeField()

    class Meta:
        ordering = ["departure_time"]

    def __str__(self):
        return (
            f"{self.route} | {str(self.departure_time)} "
            f"— {str(self.arrival_time)}"
        )


class Order(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return str(self.created_at)


class Ticket(models.Model):
    cargo = models.IntegerField()
    seat = models.IntegerField()
    journey = models.ForeignKey(
        Journey,
        related_name="tickets",
        on_delete=models.CASCADE
    )
    order = models.ForeignKey(
        Order,
        related_name="tickets",
        on_delete=models.CASCADE
    )

    @staticmethod
    def validate_ticket(cargo, seat, train, error_to_raise):
        for ticket_attr_value, ticket_attr_name, train_attr_name in [
            (cargo, "cargo", "cargo_num"),
            (seat, "seat", "places_in_cargo"),
        ]:
            count_attrs = getattr(train, train_attr_name)
            if not (1 <= ticket_attr_value <= count_attrs):
                raise error_to_raise(
                    {
                        ticket_attr_name: f"{ticket_attr_name} "
                        f"number must be in available range: "
                        f"(1, {train_attr_name}): "
                        f"(1, {count_attrs})"
                    }
                )

    def clean(self):
        Ticket.validate_ticket(
            self.cargo,
            self.seat,
            self.journey.train,
            ValidationError,
        )

    def save(
        self,
        force_insert=False,
        force_update=False,
        using=None,
        update_fields=None,
    ):
        self.full_clean()
        return super(Ticket, self).save(
            force_insert=force_insert,
            force_update=force_update,
            using=using,
            update_fields=update_fields
        )

    class Meta:
        unique_together = ("journey", "cargo", "seat")
        ordering = ["seat"]

    def __str__(self):
        return (
            f"Route: {self.journey.route}\n"
            f"Cargo: {self.cargo} | Seat: {self.seat}\n"
            f"Departure time: {str(self.journey.departure_time)}\n"
            f"Arrival time: {str(self.journey.arrival_time)}"
        )
