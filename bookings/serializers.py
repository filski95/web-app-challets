from datetime import date, datetime, timedelta

from rest_framework import serializers

from . import exceptions
from .models import ChalletHouse, CustomerProfile, Opinion, Reservation, Suggestion


class CustomerProfileSerializer(serializers.HyperlinkedModelSerializer):

    user = serializers.HyperlinkedRelatedField(read_only=True, view_name="accounts:user_detail", lookup_field="slug")
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:single_customer")

    class Meta:
        model = CustomerProfile
        fields = ("joined", "status", "total_visits", "user", "url")


class SuggestionSerializer(serializers.ModelSerializer):

    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:suggestion_detail")
    author = serializers.SlugRelatedField(read_only=True, slug_field="full_name")  # property used

    class Meta:
        model = Suggestion
        fields = ("title", "main_text", "image", "url", "author")


class OpinionSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:opinion_detail")
    author = serializers.SlugRelatedField(read_only=True, slug_field="full_name")  # property used

    class Meta:
        model = Opinion
        fields = ("title", "main_text", "image", "name", "surname", "author", "url")


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

        new_reservation_days = [str(start + timedelta(days=day)) for day in range((end - start).days + 1)]
        taken_spots = selected_house.house_reservations.house_spots(selected_house.house_number)

        # try except block in case it is the first registration and taken_spots is empty.
        try:
            if end < taken_spots[0] or start > taken_spots[-1]:
                return True
            else:
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
        # obj = validated_data.get("obj")

        if new_status == 9:
            instance.start_date = None
            instance.end_date = None
            instance.status = new_status
            instance.nights = 0
        else:
            instance.status = new_status

        instance.save(cancellation=new_status)
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
        """
        - customerprofile field to be visible only for users with admin status.
        """
        fields = super().get_fields(*args, **kwargs)
        fields.pop("id")  # dont want to have id displayed anywhere

        return fields


class ChalletHouseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="bookings:challet_house")
    house_reservations = BasicReservationSerializer(many=True, not_allowed_fields=["id", "house"])
    already_reserved_nights = serializers.SerializerMethodField()

    class Meta:
        model = ChalletHouse
        fields = ("house_number", "price_night", "url", "already_reserved_nights", "house_reservations")

    def get_already_reserved_nights(self, obj):

        house = ChalletHouse.objects.get(house_number=obj.house_number)
        taken_spots = house.house_reservations.house_spots(house.house_number)

        return taken_spots
