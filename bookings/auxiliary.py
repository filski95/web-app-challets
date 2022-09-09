from datetime import date, timedelta

from accounts.models import MyCustomUser
from django.db import models
from django.db.models import Q


def get_sentinel_user():
    return MyCustomUser.objects.get(email="sentinel_user@gmail.com", name="Anonimowy", surname="Uzytkownik")


# TODO try to figure out a queryset for returning all free days for a given house
class ChalletSpotQuerySet(models.Manager):
    def house_spots(self, house_number):
        # ignore all canceleed reservations
        queryset = self.filter(Q(house=house_number) & ~Q(start_date=None)).order_by("start_date")
        taken_spots = self._date_ranges(queryset)
        return {house_number: taken_spots}

    def _date_ranges(self, queryset):
        all_taken_days = []
        for reservation in queryset:

            start = reservation.start_date
            end = reservation.end_date
            difference = end - start

            days = [
                start + timedelta(days=day)
                for day in range(difference.days)
                if (start + timedelta(days=day) >= date.today())
            ]
            all_taken_days.extend(days)

        return all_taken_days
