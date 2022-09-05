from django_filters import rest_framework as filters

from .models import MyCustomUser


class UserFilter(filters.FilterSet):
    class Meta:
        model = MyCustomUser
        fields = {"name": ["exact"], "email": "", "date_of_birth": ["lte", "gte", "exact"]}
