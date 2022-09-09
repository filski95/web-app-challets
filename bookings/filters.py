from django import forms
from django_filters import rest_framework as filters
from django_filters.widgets import SuffixedMultiWidget

from .models import ChalletHouse, Opinion, Reservation, Suggestion

# class NightsTriWidget(SuffixedMultiWidget):
#     suffixes = ["lte", "gte", "equal"]

#     def __init__(self, attrs=None):

#         widgets = [
#             forms.NumberInput(attrs={"placeholder": "lte"}),
#             forms.NumberInput(attrs={"placeholder": "exact"}),
#             forms.NumberInput(attrs={"placeholder": "equal"}),
#         ]

#         super().__init__(widgets, attrs)


# class NightsTriField(forms.MultiValueField):
#     widget = NightsTriWidget

#     def __init__(self, fields=None, *args, **kwargs):
#         if fields is None:
#             fields = [
#                 forms.IntegerField(min_value=0),
#                 forms.IntegerField(min_value=0),
#                 forms.IntegerField(min_value=0),
#             ]
#         super().__init__(fields, *args, **kwargs)

#     def compress(self, data_list):

#         if data_list:
#             return data_list
#         return [None, None, None]


# class NightsTriFilter(filters.Filter):

#     field_class = NightsTriField

#     def filter(self, qs, value):
#         raise NotImplementedError("implement the method on the FilterSet class")


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

    # nights_taken = NightsTriFilter(label="nights_taken", method="filter_nights")

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

    # def filter_nights(self, queryset, name, value):

    # method based on the filter. Not implemented as the fields on the NightsTriField are not displayed as expected
    # it is simply not transparent enough and not worth the hustle. Stick to 3 fields and one method -> calculate_nights
    # code left for future reference.

    #     return queryset


class ReservationFilter(filters.FilterSet):
    class Meta:
        model = Reservation
        fields = {
            "reservation_number": ["exact"],
            "house": ["exact"],
            "status": ["exact"],
            "start_date": ["gte", "lte"],
        }


class OpinionFilter(filters.FilterSet):
    class Meta:
        model = Opinion
        fields = {
            "title": ["icontains"],
            "author": ["exact"],
            "name": ["exact", "icontains"],
            "surname": ["exact", "icontains"],
        }


class SuggestionFilter(filters.FilterSet):
    class Meta:
        model = Suggestion
        fields = {
            "title": ["exact", "icontains"],
            "author": ["exact"],
        }
