from datetime import timedelta

from django.utils import timezone

from railway.models import (
    Station,
    Route,
    TrainType,
    Train,
    Crew,
    Journey,
    Order,
    Ticket
)


def sample_station(**params):
    defaults = {
        "name": "Kyiv",
        "latitude": 50.44,
        "longitude": 30.49
    }
    defaults.update(params)

    return Station.objects.create(**defaults)


def sample_route(**params):
    if "distance" not in params:
        params["distance"] = 300
    if "source" not in params:
        params["source"] = sample_station(name="Dnipro")
    if "destination" not in params:
        params["destination"] = sample_station(name="Lviv")

    return Route.objects.create(**params)


def sample_train_type(**params):
    defaults = {
        "name": "Fast"
    }
    defaults.update(params)

    return TrainType.objects.create(**defaults)


def sample_train(**params):
    if "name" not in params:
        params["name"] = "Capital-091"
    if "cargo_num" not in params:
        params["cargo_num"] = 14
    if "places_in_cargo" not in params:
        params["places_in_cargo"] = 36
    if "train_type" not in params:
        params["train_type"] = sample_train_type()

    return Train.objects.create(**params)


def sample_crew(**params):
    defaults = {
        "first_name": "Anna",
        "last_name": "Zebrova"
    }
    defaults.update(params)

    return Crew.objects.create(**defaults)


def sample_journey(**params):
    if "route" not in params:
        params["route"] = sample_route()
    if "train" not in params:
        params["train"] = sample_train()
    if "departure_time" not in params:
        params["departure_time"] = timezone.now()
    if "arrival_time" not in params:
        params["arrival_time"] = timezone.now() + timedelta(days=1)

    return Journey.objects.create(**params)


def sample_order(user):
    return Order.objects.create(user=user)


def sample_ticket(order, **params):
    if "cargo" not in params:
        params["cargo"] = 1
    if "seat" not in params:
        params["seat"] = 1
    if "journey" not in params:
        params["journey"] = sample_journey()

    return Ticket.objects.create(order=order, **params)
