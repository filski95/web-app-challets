from django.contrib import admin

from bookings.models import CustomerProfile, Opinion, Reservation, Suggestion


class CustomerInline(admin.StackedInline):
    """
    This class becomes a part of the MyCustomUser section in the admin.
    readonly_fields let non editable fields to be visible there as well.
    """

    model = CustomerProfile
    verbose_name_plural = "Customers"
    readonly_fields = ("surname", "first_name", "joined")


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


# @admin.register(Opinion)
# class OpinionAdmin(admin.ModelAdmin):
#     list_display = ["title"]


admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(Reservation)
admin.site.register(Opinion)
admin.site.register(Suggestion)
