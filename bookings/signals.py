import datetime

from accounts.models import MyCustomUser
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token

from bookings.models import Reservation

from .models import CustomerProfile, ReservationConfrimation
from .tasks import send_email_notification_reservation, send_order_confirmation_task


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


@receiver(post_save, sender=Reservation)
def reservation_confirmation(sender, instance, created, **kwargs):
    """this function must be placed below update_reservation_number -> to avoid reservation_number = None"""

    if created:
        confirmation = ReservationConfrimation.objects.create(reservation=instance)

    else:
        #     # if updated (status change)
        #     # for some reason, two signals are being generated and the first one makes "created" false.
        #     # without this try except block code could fail as we would try to queyr object that is techinically not there yet
        try:
            confirmation = ReservationConfrimation.objects.get(reservation=instance)
            # 0 is a default status, without this if block, program would generate two emails with the same attachment
            # upon creation of a reservation. This is because the func update_reservation_number ends up with a save on the Reservation model.
            # that means that there are 2 post_save calls, once with created=True, and once with False.
            # False would ideally mean = update, but it is not due to this issue. Since 0 is a default status,
            # here it is assumed that the reservation was just created and we can skip sending a new email
            if confirmation.reservation.status == 0:
                return

        except ObjectDoesNotExist:
            return
        confirmation.save()


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


@receiver(post_save, sender=ReservationConfrimation)
def send_order_confrimation(sender, instance, created, **kwargs):

    # dont send new confirmations for completed/not confirmed if not created signal
    # for 99 status (after customer came back home) its meaningless
    # and the other one would be a reconfirmation which is not needed either.
    if created is True or instance.reservation.status not in [0, 99]:
        id = instance.id
        send_order_confirmation_task.apply_async((id,), countdown=0)
