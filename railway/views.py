from django.db.models import Count, F
from django_filters import rest_framework as filters
from drf_spectacular.utils import OpenApiParameter, extend_schema
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

    def list(self, request, *args, **kwargs):
        """Get a list of stations."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a station."""
        return super().create(request, *args, **kwargs)


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

    def list(self, request, *args, **kwargs):
        """Get a list of routes."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a route."""
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Get a route by id."""
        return super().retrieve(request, *args, **kwargs)


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

    def list(self, request, *args, **kwargs):
        """Get a list of train types."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a train type."""
        return super().create(request, *args, **kwargs)


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

    def list(self, request, *args, **kwargs):
        """Get a list of trains."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a train."""
        return super().create(request, *args, **kwargs)


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

    def list(self, request, *args, **kwargs):
        """Get a list of crews."""
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a crew member."""
        return super().create(request, *args, **kwargs)


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

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="departure_date",
                type={"type": "string"},
                description=(
                    "Filter by journey departure date "
                    "(ex. ?departure_date=2026-05-13)"
                ),
            ),
            OpenApiParameter(
                name="source",
                type={"type": "string"},
                description="Filter by journey source (ex. ?source=Lviv)",
            ),
            OpenApiParameter(
                name="destination",
                type={"type": "string"},
                description=(
                    "Filter by journey destination "
                    "(ex. ?destination=Kyiv)"
                ),
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Get a list of journeys."""
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Get a journey by id."""
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a journey."""
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update journey by id."""
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update journey by id."""
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete journey by id."""
        return super().destroy(request, *args, **kwargs)


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

    def list(self, request, *args, **kwargs):
        """Get a list of orders."""
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Get a order by id."""
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """Create a order."""
        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        """Update order by id."""
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        """Partial update order by id."""
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """Delete order by id."""
        return super().destroy(request, *args, **kwargs)
