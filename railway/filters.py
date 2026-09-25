from django_filters import rest_framework as filters

from railway.models import Journey


class JourneyFilter(filters.FilterSet):
    departure_date = filters.DateFilter(
        field_name="departure_time",
        lookup_expr="date"
    )
    source = filters.CharFilter(
        field_name="route__source__name",
        lookup_expr="icontains"
    )
    destination = filters.CharFilter(
        field_name="route__destination__name",
        lookup_expr="icontains"
    )

    class Meta:
        model = Journey
        fields = ("departure_date", "source", "destination")
