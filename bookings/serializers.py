from accounts.models import MyCustomUser
from rest_framework import serializers

from .models import CustomerProfile, Opinion, Suggestion


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

    class Meta:
        model = Opinion
        fields = ("title", "main_text", "image", "name", "surname", "url")
