from django.urls import path, include
from rest_framework import routers

from railway.views import (
    StationViewSet,
    RouteViewSet,
    TrainTypeViewSet,
    TrainViewSet,
    CrewViewSet,
    JourneyViewSet,
    OrderViewSet,
)


router = routers.DefaultRouter()
router.register("stations", StationViewSet, basename="stations")
router.register("routes", RouteViewSet, basename="routes")
router.register("train-types", TrainTypeViewSet, basename="train-types")
router.register("trains", TrainViewSet, basename="trains")
router.register("crews", CrewViewSet, basename="crews")
router.register("journeys", JourneyViewSet, basename="journeys")
router.register("orders", OrderViewSet, basename="orders")

urlpatterns = [path("", include(router.urls))]

app_name = "railway"
