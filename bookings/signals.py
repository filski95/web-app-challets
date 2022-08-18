from accounts.models import MyCustomUser
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CustomerProfile


@receiver(post_save, sender=MyCustomUser)
def create_profile(sender, instance, created, **kwargs):
    """profile is created right after user"""
    if created:
        CustomerProfile.objects.create(user=instance, first_name=instance.name, surname=instance.surname)


@receiver(post_save, sender=MyCustomUser)
def update_profiles(sender, instance, created, **kwargs):

    if not created:
        # get name and surname out of the queryset (1 item only)
        # MyCustomUser.objects.select_related("customerprofile").filter(id=instance.id)

        user_name, user_surname = MyCustomUser.objects.filter(id=instance.id).values_list("name", "surname")[0]
        name, surname = CustomerProfile.objects.filter(user__id=instance.id).values_list("first_name", "surname")[0]

        if user_name != name:
            instance.customerprofile.first_name = user_name
        if user_surname != surname:
            instance.customerprofile.surname = user_surname

        instance.customerprofile.save()
