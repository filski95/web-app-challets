from datetime import date, timedelta

from accounts.models import MyCustomUser
from django.db import connection, models, reset_queries
from django.db.models import F, Q
from rest_framework.throttling import UserRateThrottle

from bookings.decorators import UpdateReservationDecorator, customer_profile_update_decorator
from bookings.utils import my_date


def get_sentinel_user():
    return MyCustomUser.objects.get(email="sentinel_user@gmail.com", name="Anonimowy", surname="Uzytkownik")


class ChalletSpotQuerySet(models.Manager):
    def house_spots(self, house_number):
        # ignore all canceleed reservations
        queryset = (
            self.select_related("house").filter(Q(house=house_number) & ~Q(start_date=None)).order_by("start_date")
        )
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


@customer_profile_update_decorator(log=True)
def update_customer_profile_status_hierarchy(customer_profile, hierarchy):
    """
    update total_visits on the customer profile, check if they should advance in ranks
    """
    customer_profile.total_visits = F("total_visits") + 1
    customer_profile.save()
    customer_profile.refresh_from_db()
    if customer_profile.status == "S":
        pass
    else:
        if customer_profile.total_visits < hierarchy["N"]:
            # N = Default
            pass
        elif customer_profile.total_visits <= hierarchy["R"]:
            customer_profile.status = "R"
        else:
            customer_profile.status = "S"
    customer_profile.save()


@UpdateReservationDecorator
def update_reservation_customerprofile(all_current_reservations, hierarchy, end_date=None):
    """
    query all current reservations [target-> end_date=today()] and check if their status is 9 or 99, (cancelled/completed)
    -> if not change status to 99
    """

    if end_date is None:
        end_date = my_date.today()

    for reservation in all_current_reservations:
        reservation.status = 99
        update_customer_profile_status_hierarchy(reservation.customer_profile, hierarchy)
        reservation.save()


class CustomUseRateThrottle(UserRateThrottle):
    rate = "100/day"

    def allow_request(self, request, view):

        if request.user.is_anonymous or request.user.is_admin is False:
            # regular and super customers do not have any limitation
            try:
                if request.user.customerprofile.status != "N":
                    return True
            except AttributeError:
                pass
            return super().allow_request(request, view)
        else:
            return True


class BurstRateThrottle(UserRateThrottle):
    scope = "burst"


class SustainedRateThrottle(UserRateThrottle):
    scope = "sustained"
