from datetime import date, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger

from bookings import auxiliary
from bookings.models import CustomerProfile, Reservation

logger = get_task_logger(__name__)


@shared_task
def run_profile_reservation_updates():
    end_date = date.today() + timedelta(10)
    customer_hierarchy = CustomerProfile.hierarchy
    all_current_reservations = (
        Reservation.objects.filter(end_date__lte=end_date)
        .exclude(status__in=[9, 99])
        .select_related("customer_profile")
    )

    auxiliary.update_reservation_customerprofile(all_current_reservations, customer_hierarchy, end_date=end_date)

    logger.info(f"{run_profile_reservation_updates.__name__} just ran.")
