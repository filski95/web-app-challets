from datetime import date, timedelta

from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.core.mail import send_mail

from bookings import auxiliary
from bookings.auxiliary import update_reservation_customerprofile
from bookings.models import CustomerProfile, Reservation

logger = get_task_logger(__name__)


@shared_task
def run_profile_reservation_updates():
    end_date = date.today() + timedelta(10)
    customer_hierarchy = CustomerProfile.hierarchy
    # excluding 9 - cancelled, 99 completed. Not confirmed are ok - we are not demanding users to confirm
    all_current_reservations = (
        Reservation.objects.filter(end_date__lte=end_date)
        .exclude(status__in=[9, 99])
        .select_related("customer_profile")
    )

    auxiliary.update_reservation_customerprofile(all_current_reservations, customer_hierarchy, end_date=end_date)

    logger.info(f"{run_profile_reservation_updates.__name__} just ran.")


@shared_task
def send_email_notification_reservation(data_celery, new_reservation_number, *args, **kwargs):
    """
    sends email notifying admin about new reservation.
    - data for the email is being created in the signals.py and passed as data_celery argument.
    this is because celerey would not allow objects to be passed in between tasks and rest (serializing error)

    * apart from that, during tests there was no way to query the freshly created reservations-> queries were sent to teh actual database
    and objectdoesnotexist error was raised [in other words -> passing id instead of objects was not helpfull.]

    ** reservation_number at the time of this function is already created but not saved.
    Consequently it is passed as a string here directly from the signal and not queries

    """

    start_date = data_celery.get("start_date")
    end_date = data_celery.get("end_date")
    reservation_number = new_reservation_number
    name = data_celery.get("name")
    surname = data_celery.get("surname")
    email = data_celery.get("email")

    subject = f"New reservation has been created: {reservation_number} [{date.today()}] "
    message = f"""
    A user: {name} {surname} has created a reservation for {start_date} - {end_date}\n
    email: {email}
    """

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[settings.NOTIFICATION_EMAIL],
        fail_silently=False,
    )

    logger.info(f"{send_email_notification_reservation.__name__} just ran")
