import io

from accounts.models import MyCustomUser
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

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
        return f"Profile of: {str(self.user).title()} [ID: {self.id}]; joined on {self.joined}"

    @property
    def profile_user_repr(self):
        return f"{self.first_name} {self.surname} [ID:{self.user.id}]"


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
    - Annonymous user will not be amendable by authors
    """

    pass


class Opinion(CommunicationBaseModel):
    # need to implement a mechanism asking for a surname/name or smth linked to reservation
    # to check validity of the person leaving the opinion
    # -> want to avoid necessity to have account/register
    # as some people may make a reservation through other source (phone)
    name = models.CharField(max_length=20, null=True, blank=True)
    surname = models.CharField(max_length=20, null=True, blank=True)
    rating = models.SmallIntegerField(
        null=True, blank=True, validators=[MaxValueValidator(limit_value=5), MinValueValidator(limit_value=1)]
    )


class ChalletHouse(models.Model):
    class Meta:
        ordering = ["house_number"]

    price_night = models.SmallIntegerField(verbose_name="price per night")
    house_number = models.PositiveSmallIntegerField(
        validators=[MaxValueValidator(limit_value=3)], primary_key=True, null=False, unique=True
    )
    address = models.CharField(max_length=120, null=False, default="Test Address 41-200")

    def __str__(self) -> str:
        return f"Domek numer {self.house_number}"


class Reservation(models.Model):
    class Meta:
        ordering = ["id"]

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

        status_change = kwargs.pop("status_change", None)
        # status_change does not require nights calculations.
        # nights might bes 0ed on the serializer update level while dates becoome None
        # if statetement below added to avoid crashes with (None - None).days
        if not status_change:
            self.nights = (self.end_date - self.start_date).days  # time delta days
        self.total_price = self.nights * self.house.price_night
        super().save(*args, **kwargs)

    def clean(self):
        # validation for admin panel
        if self.start_date >= self.end_date:
            raise ValidationError("End date must be later than start date")


class ReservationConfrimation(models.Model):
    reservation = models.OneToOneField(Reservation, on_delete=models.CASCADE)
    saved_file = models.FileField(null=True, upload_to="confirmations/")

    def save(self, *args, **kwargs):

        self._create_pdf(self.reservation)

        super().save(*args, **kwargs)

    def _create_pdf(self, reservation):

        res = reservation
        file = io.BytesIO()
        c = canvas.Canvas(file, pagesize=letter, bottomup=1, verbosity=0)
        w, h = letter  # [612/792]
        # draw two lines at the top and bottom of the document. Entire witdth
        c.line(0, 750, w, 750)
        c.line(0, 50, w, 50)
        # draw an address above the first line to the left
        c.drawString(20, 780, f"{res.house.address}")
        c.drawString(w - 200, 780, f"Created at: {res.created_at.replace(microsecond=0,tzinfo=None)}")

        # write a string centered based on the middle [w/2]
        c.drawCentredString(w / 2, 730, f"RESERVATION: {res.reservation_number}")

        lines = {
            "Guest": res.reservation_owner.full_name,
            "Check in": res.start_date,
            "Check out": res.end_date,
            "Number of nights": res.nights,
            "House number": res.house.house_number,
            "Total price": res.total_price,
            "Status": res.get_status_display(),
        }

        if res.status == 0:
            lines.update(
                {
                    "*": "Please confirm your reservation on the website as soon as you are certain about your stay. Thank you!"
                }
            )

        # below moves the cursor after text is drawn
        main_text_object = c.beginText()
        main_text_object.setTextOrigin(50, 640)
        main_text_object.setFont("Helvetica-Oblique", 14)

        for title, value in lines.items():
            if title == "*":
                s = str(title) + str(value)
                main_text_object.setFillGray(0.4)
                main_text_object.setFont("Helvetica-Oblique", 11)
            else:
                s = str(title) + ": " + str(value)
            main_text_object.textLine(s)
        c.drawText(main_text_object)
        c.save()

        file.name = f"{reservation.reservation_number}.pdf"

        self.saved_file = File(file)
