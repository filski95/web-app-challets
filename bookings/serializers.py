from datetime import date, datetime, timedelta

from rest_framework import serializers

from . import exceptions
from .models import ChalletHouse, CustomerProfile, Opinion, Reservation, Suggestion


class CustomerProfileSerializer(serializers.HyperlinkedModelSerializer):

    user = serializers.HyperlinkedRelatedField(read_only=True, view_name="accounts:user_detail", lookup_field="slug")
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:single_customer")
    reservation_set = serializers.HyperlinkedRelatedField(
        many=True, read_only=True, view_name="bookings:reservation_detail"
    )

    class Meta:
        model = CustomerProfile
        fields = ("joined", "status", "total_visits", "user", "url", "reservation_set")


# below replaced by ordering on the reservation model. Possible performance issues as ordering is on server and not db
# def to_representation(self, instance):
#     response = super().to_representation(instance)
#     response["reservation_set"] = sorted(response["reservation_set"], key=lambda x: x[-4:-1])
#     return response


class SuggestionSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:suggestion_detail")
    author = serializers.SlugRelatedField(read_only=True, slug_field="full_name")  # property used

    class Meta:
        model = Suggestion
        fields = ("title", "main_text", "image", "url", "author", "provided_on", "edited_on")


class OpinionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:opinion_detail")
    author = serializers.SlugRelatedField(read_only=True, slug_field="full_name")  # property used

    class Meta:
        model = Opinion
        fields = ("title", "main_text", "image", "name", "surname", "author", "url", "provided_on", "edited_on")

    def get_fields(self, *args, **kwargs):
        """
        logged in user does not have the option to provie user name and surname. List view [GET] does not show name and surname
        -> Only "Anonimowy Uzytkownik", so the sentinel user
        """
        fields = super().get_fields(*args, **kwargs)

        if self.context.get("request").user.is_authenticated or self.context.get("request").method == "GET":
            fields.pop("name")
            fields.pop("surname")
            return fields
        return fields


class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """
    A ModelSerializer that takes an additional `not_allowed_fields` argument that
    controls which fields should be displayed.

    """

    def __init__(self, *args, **kwargs):
        """
        changed implementation comparing to docs; not allowed fields
        - not_allowed_field works similarly to original implementation except the condition and set operation is "amended"
        all fields added to this list of arguments are removed from the final fields list.

        """
        # Don't pass the 'not_allowed_fields arg  to the superclass
        not_allowed_fields = kwargs.pop("not_allowed_fields", None)
        # Instantiate the superclass normally
        super().__init__(*args, **kwargs)
        if not_allowed_fields is not None:
            # Drop any fields that are specified`by fields argument argument.
            not_allowed = set(not_allowed_fields)
            existing = set(self.fields)
            for field_name in existing & not_allowed:
                self.fields.pop(field_name)


class ReservationSerializer(DynamicFieldsModelSerializer):
    customer_profile = serializers.StringRelatedField()
    # https://docs.djangoproject.com/en/1.11/ref/models/instances/#django.db.models.Model.get_FOO_display
    status = serializers.ChoiceField(choices=Reservation.STATUS_CHOICES, source="get_status_display", read_only=True)
    reservation_owner = serializers.HyperlinkedRelatedField(
        read_only=True, view_name="accounts:user_detail", lookup_field="slug"
    )

    class Meta:
        model = Reservation
        fields = "__all__"
        read_only_fields = ["nights", "total_price", "reservation_number"]

    def validate(self, attrs):
        # default values assigned in case the serializer is only called when confirming status on the reservation
        # DetailViwReservationSerializer has only 1 field writable - status.

        start = attrs.get("start_date", 0)
        end = attrs.get("end_date", 1)

        self._check_if_dates_make_sense(start, end)

        self._check_if_no_overlaping_days(attrs, start, end)

        attrs = self._fix_get_status_display_to_status(attrs)

        return attrs

    def _check_if_no_overlaping_days(self, attrs, start, end):
        """
        checks if this is creation of new reservations. If so, checks if dates on the reservation are available
        and raises appropriate exception if not. If this is not a new reservation then house attribute will not be present
        and this function will return True
        """
        # house will be in the attributes list only during creation of the reservation
        # house will already be an instance of ChalletHouse.
        selected_house = attrs.get("house", None)
        if selected_house is None:
            return True

        new_reservation_days = [start + timedelta(days=day) for day in range((end - start).days + 1)]
        # {house_nb: list_of_dates}
        taken_spots = selected_house.house_reservations.house_spots(selected_house.house_number)

        # try except block in case it is the first registration and taken_spots is empty.
        try:
            # for 1 night reservations only check first date - the latter will be leaving date so someone can arrive that day in the afternoon
            if len(new_reservation_days) == 2:
                if new_reservation_days[0] not in taken_spots.get(selected_house.house_number):
                    return True
            # otherwise check first and the last one quickly (reservations outside of current range)
            elif (
                end < taken_spots.get(selected_house.house_number)[0]
                or start >= taken_spots.get(selected_house.house_number)[-1]
            ):
                return True

            else:
                # first day may overlap -> end date = leave so we can have someone leaving and comming in on the same day
                if new_reservation_days[1] not in taken_spots.get(
                    selected_house.house_number
                ) and new_reservation_days[-1] not in taken_spots.get(selected_house.house_number):

                    return True

            raise exceptions.DatesNotAvailable(days=new_reservation_days)  # days att might be ditched if too exp.
        except IndexError:
            pass

    def _check_if_dates_make_sense(self, start, end):
        """end date must be higher than start date"""

        if start >= end:
            raise serializers.ValidationError("End date must be later than start date")
        if not isinstance(start, int):
            if start < date.today():
                raise serializers.ValidationError("Dates must be in the future!")

    def _fix_get_status_display_to_status(self, attrs):
        """change get_status_display name into status"""

        # due to the source argument and get_FOO_display on th serializer, create method receives: get_status_display
        # as if that was a field.. fix below:
        status_value = attrs.pop("get_status_display", None)
        if status_value is None:
            return attrs

        status = {"status": status_value}
        attrs.update(status)
        return attrs


class BasicReservationSerializer(ReservationSerializer):
    """
    basic serializer for list views only, contains only basic info
    """

    reservation_url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:reservation_detail")

    class Meta:
        model = Reservation
        fields = [
            "reservation_number",
            "customer_profile",
            "start_date",
            "end_date",
            "house",
            "status",
            "reservation_url",
        ]

    def get_fields(self, *args, **kwargs):

        fields = super().get_fields(*args, **kwargs)
        from_challet_list = self.context.get("remove_house")
        user = self.context.get("request").user

        # dont show customer_profiel field to no admins
        if not user.is_admin:
            fields.pop("customer_profile")

        # house irrelevant in the challet list -> linked to one anyway
        if from_challet_list:
            fields.pop("house")
        return fields


class DetailViewReservationSerializer(ReservationSerializer):
    """
    serializer created specificaly for detail view of reservations.
    all fields are read only - apart from status -> allow confirmations / cancellations
    """

    class Meta:
        model = Reservation
        fields = "__all__"

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)
        for field in self.fields:
            if field == "status":
                self.fields[field].read_only = False
            else:
                self.fields[field].read_only = True

    def update(self, instance, validated_data):
        new_status = validated_data.get("status")

        if new_status == 9:
            instance.start_date = None
            instance.end_date = None
            instance.status = new_status
            instance.nights = 0
        else:
            instance.status = new_status

        instance.save(status_change=new_status)
        return instance

    def validate_status(self, value):
        instance = getattr(self, "instance", None)
        if instance:
            if instance.status == 1 and value == 0:
                raise serializers.ValidationError(
                    "You cannot set the status to 'not confirmed' on a confirmed reservation, choose cancel if you wish to resign"
                )
            if instance.status == 9:
                raise serializers.ValidationError("Cancellation of a reservation cannot be reverted!")
        return value

    def get_fields(self, *args, **kwargs):

        fields = super().get_fields(*args, **kwargs)
        fields.pop("id")  # dont want to have id displayed anywhere

        user = self.context.get("request").user
        if not user.is_admin:
            fields.pop("customer_profile")

        return fields


import calendar
import time
from collections import OrderedDict


class ChalletHouseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:challet_house")
    # house_reservations = BasicReservationSerializer(many=True, not_allowed_fields=["id", "house"])
    house_reservations = serializers.SerializerMethodField()
    already_reserved_nights = serializers.SerializerMethodField()
    free_spots_this_year = serializers.SerializerMethodField()

    class Meta:
        model = ChalletHouse
        fields = (
            "house_number",
            "price_night",
            "url",
            "already_reserved_nights",
            "free_spots_this_year",
            "house_reservations",
        )

    def get_already_reserved_nights(self, obj):

        house = ChalletHouse.objects.get(house_number=obj.house_number)
        taken_spots = house.house_reservations.house_spots(house.house_number)

        return taken_spots[obj.house_number]

    def get_house_reservations(self, obj):
        """
        house reservations will display reservations to their owners only..
        Admins will see all reservations [replacing nested serializer with this method to enable this "feature"]
        """
        user = self.context.get("request").user
        serializer_context = {"remove_house": True, "request": self.context.get("request")}

        if not user.is_authenticated:
            reservations = []
            serializer = BasicReservationSerializer(reservations, many=True, context=serializer_context)
        elif user.is_admin:
            reservations = Reservation.objects.filter(house=obj)
            serializer = BasicReservationSerializer(reservations, many=True, context=serializer_context)
        else:
            reservations = Reservation.objects.filter(reservation_owner=user, house=obj)
            serializer = BasicReservationSerializer(reservations, many=True, context=serializer_context)

        return serializer.data

    def get_free_spots_this_year(self, obj):

        taken_spots = obj.house_reservations.house_spots(obj.house_number)
        # taken_spots = taken_spots[obj.house_number]
        taken_spots_dict = OrderedDict()

        # dict for O(1) lookups later
        for day in taken_spots[obj.house_number]:
            taken_spots_dict[day] = True

        current_year = date.today().year
        current_month = date.today().month
        all_days_till_next_year = []
        c = calendar.Calendar()

        for i in range(current_month, 13):
            weeks_month = c.monthdatescalendar(current_year, current_month)
            for one_week in weeks_month:
                all_days_till_next_year.extend(one_week)
            current_month += 1

        free_days = []
        # taken spots returns days in order
        # https://stackoverflow.com/questions/10058140/accessing-items-in-an-collections-ordereddict-by-index
        # below allows to get first value to check against without the need to create entire list.
        first_day_taken = next(iter(taken_spots_dict.keys()))
        # append all days which are not listed in taken_spots to free days list
        for day in all_days_till_next_year:
            if day < first_day_taken:
                continue
            else:
                if day in taken_spots:
                    continue
                else:
                    free_days.append(day)

        return free_days


class RunUpdatesSerializer(serializers.Serializer):

    run_updates = serializers.BooleanField(default=False)
