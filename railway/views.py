from django.db.models import Count, F
from django_filters import rest_framework as filters
from rest_framework import viewsets, mixins
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated

from railway.filters import JourneyFilter
from railway.mixins import UploadImageMixin
from railway.permissions import IsAdminOrIfAuthenticatedReadOnly

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
    TrainTypeImageSerializer,
    TrainSerializer,
    TrainListSerializer,
    CrewSerializer,
    CrewImageSerializer,
    JourneySerializer,
    JourneyListSerializer,
    JourneyDetailSerializer,
    OrderSerializer,
    OrderListSerializer,
    OrderDetailSerializer,
)


class StationViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Station.objects.all()
    serializer_class = StationSerializer
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)


class RouteViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Route.objects.select_related(
        "source", "destination"
    )
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):

        if self.action == "list":
            return RouteListSerializer

        if self.action == "retrieve":
            return RouteDetailSerializer

        return RouteSerializer


class TrainTypeViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    UploadImageMixin,
    viewsets.GenericViewSet,
):
    queryset = TrainType.objects.all()
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):

        if self.action == "upload_image":
            return TrainTypeImageSerializer

        return TrainTypeSerializer


class TrainViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Train.objects.select_related("train_type")
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):

        if self.action == "list":
            return TrainListSerializer

        return TrainSerializer


class CrewViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    UploadImageMixin,
    viewsets.GenericViewSet,
):
    queryset = Crew.objects.all()
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)

    def get_serializer_class(self):

        if self.action == "upload_image":
            return CrewImageSerializer

        return CrewSerializer


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
    permission_classes = (IsAdminOrIfAuthenticatedReadOnly,)
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = JourneyFilter

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
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = queryset.filter(user=self.request.user)

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
