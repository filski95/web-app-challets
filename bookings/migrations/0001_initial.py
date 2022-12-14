# Generated by Django 4.1 on 2022-08-30 07:01

import bookings.auxiliary
from django.conf import settings
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ChalletHouse",
            fields=[
                (
                    "price_night",
                    models.SmallIntegerField(verbose_name="price per night"),
                ),
                (
                    "house_number",
                    models.PositiveSmallIntegerField(
                        primary_key=True,
                        serialize=False,
                        unique=True,
                        validators=[
                            django.core.validators.MaxValueValidator(limit_value=3)
                        ],
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CustomerProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "total_visits",
                    models.SmallIntegerField(
                        default=0, verbose_name="Number of visits so far"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("N", "New Customer"),
                            ("R", "Regular Customer"),
                            ("S", "Super Customer"),
                        ],
                        default="N",
                        max_length=1,
                    ),
                ),
                (
                    "joined",
                    models.DateField(
                        auto_now_add=True, verbose_name="Date when customer joined"
                    ),
                ),
                (
                    "first_name",
                    models.CharField(editable=False, max_length=20, null=True),
                ),
                ("surname", models.CharField(editable=False, max_length=20, null=True)),
                (
                    "user",
                    models.OneToOneField(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Suggestion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=50)),
                (
                    "main_text",
                    models.TextField(max_length=2000, verbose_name="message content"),
                ),
                ("image", models.ImageField(blank=True, upload_to="")),
                ("provided_on", models.DateField(auto_now_add=True)),
                ("edited_on", models.DateField(auto_now=True)),
                (
                    "author",
                    models.ForeignKey(
                        default=bookings.auxiliary.get_sentinel_user,
                        on_delete=django.db.models.deletion.SET_DEFAULT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Reservation",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "status",
                    models.SmallIntegerField(
                        blank=True,
                        choices=[
                            (1, "Reservation confirmed"),
                            (0, "Reservation not confirmed"),
                            (9, "Reservation has been cancelled"),
                        ],
                        default=0,
                    ),
                ),
                ("start_date", models.DateField(help_text="Beginning of your stay")),
                (
                    "end_date",
                    models.DateField(help_text="Last day of your stay/departure"),
                ),
                ("nights", models.PositiveSmallIntegerField(blank=True)),
                ("total_price", models.SmallIntegerField(blank=True)),
                (
                    "reservation_number",
                    models.CharField(blank=True, max_length=20, null=True, unique=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "customer_profile",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="bookings.customerprofile",
                    ),
                ),
                (
                    "house",
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="house_reservations",
                        to="bookings.challethouse",
                    ),
                ),
                (
                    "reservation_owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reservations",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Opinion",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("title", models.CharField(max_length=50)),
                (
                    "main_text",
                    models.TextField(max_length=2000, verbose_name="message content"),
                ),
                ("image", models.ImageField(blank=True, upload_to="")),
                ("provided_on", models.DateField(auto_now_add=True)),
                ("edited_on", models.DateField(auto_now=True)),
                ("name", models.CharField(blank=True, max_length=20, null=True)),
                ("surname", models.CharField(blank=True, max_length=20, null=True)),
                (
                    "author",
                    models.ForeignKey(
                        default=bookings.auxiliary.get_sentinel_user,
                        on_delete=django.db.models.deletion.SET_DEFAULT,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
