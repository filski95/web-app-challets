from django.contrib import admin

from bookings.models import ChalletHouse, CustomerProfile, Opinion, Reservation, Suggestion


class CustomerInline(admin.StackedInline):
    """
    This class becomes a part of the MyCustomUser section in the admin.
    readonly_fields let non editable fields to be visible there as well.
    """

    model = CustomerProfile
    verbose_name_plural = "Customers"
    readonly_fields = ("surname", "first_name", "joined", "status")


class CustomerProfileAdmin(admin.ModelAdmin):
    list_display = [
        "first_name",
        "surname",
        "joined",
        "user",
        "status",
        "total_visits",
        "id",
    ]


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    readonly_fields = ["nights", "total_price", "reservation_number"]


admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(Opinion)
admin.site.register(Suggestion)
admin.site.register(ChalletHouse)
