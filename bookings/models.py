from accounts.models import MyCustomUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator
from django.db import models

from . import auxiliary


class CustomerProfile(models.Model):
    # hierarchy deployed in other modules when changing statuses
    hierarchy = {"N": 4, "R": 10, "S": 11}
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
        return f"Profile of: {str(self.user).title()} [ID: {self.user.id}]; joined on {self.joined}"

    @property
    def full_name(self):
        return f"{self.frist_name} {self.surname}"


class CommunicationBaseModel(models.Model):
    title = models.CharField(max_length=50)
    main_text = models.TextField(max_length=2000, verbose_name="message content")
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, default=auxiliary.get_sentinel_user, on_delete=models.SET_DEFAULT
    )
    image = models.ImageField(blank=True)
    provided_on = models.DateField(auto_now_add=True)
    edited_on = models.DateField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"A/an {self.__class__.__name__}; Author: {self.author}; Title: {self.title}; ID: {self.id}"


class Suggestion(CommunicationBaseModel):
    """
    - virtually anyone can send a suggestion
    - list views will be visible to admin only, but users will be able to see their suggestions.
    - Annonymous user will not have amendable by authors
    """

    pass


class Opinion(CommunicationBaseModel):
    # need to implement a mechanism asking for a surname/name or smth linked to reservation
    # to check validity of the person leaving the opinion
    # -> want to avoid necessity to have account/register
    # as some people may make a reservation through other source (phone)
    name = models.CharField(max_length=20, null=True, blank=True)
    surname = models.CharField(max_length=20, null=True, blank=True)


class ChalletHouse(models.Model):
    price_night = models.SmallIntegerField(verbose_name="price per night")
    house_number = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(limit_value=3)], primary_key=True, null=False, unique=True
    )

    def __str__(self) -> str:
        return f"Domek numer {self.house_number}"


class Reservation(models.Model):
    CONFIRMED = 1
    NOT_CONFIRMED = 0
    CANCELLED = 9
    COMPLETED = 99

    STATUS_CHOICES = [
        (CONFIRMED, "Reservation confirmed"),
        (NOT_CONFIRMED, "Reservation not confirmed"),
        (CANCELLED, "Reservation is cancelled"),
        (COMPLETED, "Reservation is completed"),
    ]

    customer_profile = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
    reservation_owner = models.ForeignKey(MyCustomUser, on_delete=models.CASCADE, related_name="reservations")
    house = models.ForeignKey(
        ChalletHouse,
        blank=True,
        on_delete=models.PROTECT,
        related_name="house_reservations",
    )
    status = models.SmallIntegerField(choices=STATUS_CHOICES, default=NOT_CONFIRMED, blank=True)

    start_date = models.DateField(null=True, blank=False, help_text="Beginning of your stay")
    end_date = models.DateField(null=True, blank=False, help_text="Last day of your stay/departure")
    nights = models.PositiveSmallIntegerField(blank=True)
    total_price = models.SmallIntegerField(blank=True)

    # signal to create date + reservation Id
    reservation_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = auxiliary.ChalletSpotQuerySet()

    def save(self, *args, **kwargs):

        cancellation = kwargs.pop("cancellation", None)
        # cancellation means that start and end date of a stay are transformed into Nones
        # calculation of nights would crash -> if stmt to avoid it
        if not cancellation:
            self.nights = (self.end_date - self.start_date).days  # time delta days
        self.total_price = self.nights * self.house.price_night
        super().save(*args, **kwargs)

    def clean(self):
        # validation for admin panel
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be later than start date")
