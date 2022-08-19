from django.apps import AppConfig
from django.db.models.signals import post_save


class BookingsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bookings"

    def ready(self) -> None:
        from . import signals
