from tabnanny import verbose

from accounts.models import MyCustomUser
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models


class CustomerProfile(models.Model):
    NEW_CUSTOMER = "N"
    REGULAR = "R"
    SUPER = "S"
    STATUS_CHOICES = [(NEW_CUSTOMER, "New Customer"), (REGULAR, "Regular Customer"), (SUPER, "Super Customer")]

    user = models.OneToOneField(MyCustomUser, null=True, on_delete=models.CASCADE)
    total_visits = models.SmallIntegerField(verbose_name="Number of visits so far", default=0)
    status = models.CharField(choices=STATUS_CHOICES, default=NEW_CUSTOMER, max_length=1)
    joined = models.DateField(auto_now_add=True, verbose_name="Date when customer joined")
    first_name = models.CharField(max_length=20, editable=False, null=True)  # from user model
    surname = models.CharField(max_length=20, editable=False, null=True)  # from user model

    def __str__(self) -> str:
        return f"Customer's profile of {self.user} who joined on {self.joined}"


class Reservation(models.Model):
    reservation_owner = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)


class CommunicationBaseModel(models.Model):
    title = models.CharField(max_length=50)
    main_text = models.TextField(max_length=2000, verbose_name="message content")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, default="Anonymous", on_delete=models.SET_DEFAULT)
    image = models.ImageField(blank=True)
    provided_on = models.DateField(auto_now_add=True)
    edited_on = models.DateField(auto_now=True)

    class Meta:
        abstract = True


class Suggestion(CommunicationBaseModel):
    # asd = models.CharField(max_length=50)
    pass


class Opinion(CommunicationBaseModel):
    # need to implement a mechanism asking for a surname/name or smth linked to reservation
    # to check validity of the person leaving the opinion
    # -> want to avoid necessity to have account/register
    # as some people may make a reservation through other source (phone)
    pass
