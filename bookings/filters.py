from django import forms
from django_filters import rest_framework as filters

from .models import ChalletHouse


class HouseFilter(filters.FilterSet):
    # annotate in the get_queryset ChalletHouseListView
    num_reservations = filters.NumberFilter(field_name="num_reservations", label="number of reservations")
    start_date_range = filters.DateRangeFilter(
        field_name="house_reservations__start_date", label="House reservations start date [range]"
    )

    nights_taken = filters.NumberFilter(
        field_name="house_reservations", method="calculate_nights", label="number of nights booked"
    )
    nights_taken__gte = filters.NumberFilter(
        field_name="house_reservations_gte", method="calculate_nights", label="number of nights booked (gte)"
    )
    nights_taken__lte = filters.NumberFilter(
        field_name="house_reservations_lte", method="calculate_nights", label="number of nights booked (lte)"
    )

    class Meta:
        model = ChalletHouse
        fields = {"house_number": ["exact"], "house_reservations__start_date": ["exact", "lte", "gte"]}

    def calculate_nights(self, queryset, name, value):
        # name attribute comes from field_name in the atrtributes section
        # sum_nights -> annotate in the querset, calculating all nights for single house

        if name[-3:] == "gte":
            queryset = queryset.filter(sum_nights__gte=value)
        elif name[-3:] == "lte":
            queryset = queryset.filter(sum_nights__lte=value)
        else:
            queryset = queryset.filter(sum_nights=value)

        return queryset
