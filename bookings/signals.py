import datetime
from tracemalloc import start

from accounts.models import MyCustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from bookings.models import Reservation

from .models import CustomerProfile
from .tasks import send_email_notification_reservation


@receiver(post_save, sender=MyCustomUser)
def create_profile(sender, instance, created, **kwargs):
    """profile is created right after user"""
    if created:
        # all users have tokens
        Token.objects.create(user=instance)
        if instance.is_staff is False:
            # only non admin users have customer profile
            CustomerProfile.objects.create(user=instance, first_name=instance.name, surname=instance.surname)


@receiver(post_save, sender=MyCustomUser)
def update_profiles(sender, instance, created, **kwargs):

    if not created and instance.is_admin is False:
        # get name and surname out of the queryset (1 item only)
        # MyCustomUser.objects.select_related("customerprofile").filter(id=instance.id)

        user_name, user_surname = MyCustomUser.objects.filter(id=instance.id).values_list("name", "surname")[0]
        name, surname = CustomerProfile.objects.filter(user__id=instance.id).values_list("first_name", "surname")[0]

        if user_name != name:
            instance.customerprofile.first_name = user_name
        if user_surname != surname:
            instance.customerprofile.surname = user_surname

        instance.customerprofile.save()


@receiver(post_save, sender=Reservation)
def update_reservation_number(sender, instance, created, **kwargs):
    """
    creating a reservation number out of todays date and id of the created reservation
    """
    if created:
        new_reservation_number = "".join(str(datetime.date.today()).split("-")) + str(instance.id)
        instance.reservation_number = new_reservation_number

        instance.save()

        data_celery = _prepare_data_for_celery_email(instance)
        send_email_notification_reservation.delay(data_celery, new_reservation_number)


def _prepare_data_for_celery_email(instance):
    customer = MyCustomUser.objects.get(id=instance.reservation_owner.id)

    data = {
        "start_date": instance.start_date,
        "end_date": instance.end_date,
        "name": customer.name,
        "surname": customer.surname,
        "email": customer.email,
    }

    return data
