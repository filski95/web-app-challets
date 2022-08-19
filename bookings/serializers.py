from rest_framework import serializers

from .models import CustomerProfile


class CustomerProfileSerializer(serializers.HyperlinkedModelSerializer):

    user = serializers.HyperlinkedRelatedField(read_only=True, view_name="accounts:user_detail", lookup_field="slug")

    class Meta:
        model = CustomerProfile
        fields = ("joined", "status", "total_visits", "user")
