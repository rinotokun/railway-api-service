from django.db.models import Count, F
from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from railway.models import (
    Station,
    Route,
    TrainType,
    Train,
    Crew,
    Journey,
    Order
)

from railway.serializers import (
    StationSerializer,
    RouteSerializer,
    RouteListSerializer,
    RouteDetailSerializer,
    TrainTypeSerializer,
    TrainSerializer,
    TrainListSerializer,
    CrewSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)


class StationViewSet(viewsets.ModelViewSet):
    queryset = Station.objects.all()
    serializer_class = StationSerializer


class RouteViewSet(viewsets.ModelViewSet):
    queryset = Route.objects.select_related(
        "source", "destination"
    )

    def get_serializer_class(self):

        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class TrainTypeViewSet(viewsets.ModelViewSet):
    queryset = TrainType.objects.all()
    serializer_class = TrainTypeSerializer


class TrainViewSet(viewsets.ModelViewSet):
    queryset = Train.objects.select_related("train_type")

    def get_serializer_class(self):

        if self.action in ("list", "retrieve"):
            return TrainListSerializer

        return TrainSerializer


class CrewViewSet(viewsets.ModelViewSet):
    queryset = Crew.objects.all()
    serializer_class = CrewSerializer


class JourneyViewSet(viewsets.ModelViewSet):
    queryset = (
        Journey.objects
        .select_related(
            "route__source",
            "route__destination",
            "train__train_type"
        )
        .prefetch_related("crew")
        .annotate(
            tickets_available=(
                F("train__cargo_num") * F("train__places_in_cargo")
                - Count("tickets")
            )
        )
    )

    def get_serializer_class(self):

        if self.action == "list":
            return JourneyListSerializer

        if self.action == "retrieve":
            return JourneyDetailSerializer

        return JourneySerializer


class OrderPagination(PageNumberPagination):
    page_size = 10
    max_page_size = 100


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    pagination_class = OrderPagination

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.action == "list":
            queryset = queryset.prefetch_related(
                "tickets__journey__route__source",
                "tickets__journey__route__destination"
            )
        if self.action == "retrieve":
            queryset = queryset.prefetch_related(
                "tickets__journey__tickets",
                "tickets__journey__crew",
                "tickets__journey__route__source",
                "tickets__journey__route__destination",
                "tickets__journey__train__train_type",
            )

        return queryset

    def get_serializer_class(self):

        if self.action == "list":
            return OrderListSerializer

        if self.action == "retrieve":
            return OrderDetailSerializer

        return OrderSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
