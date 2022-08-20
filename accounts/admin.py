from bookings.admin import CustomerInline
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import CustomUserChangeForm, CustomUserCreationForm
from .models import MyCustomUser


class UserAdmin(BaseUserAdmin):
    # The forms to add and change user instances
    inlines = (CustomerInline,)  # necessary to see a profile model in the admin panel under MyCustomUser
    form = CustomUserChangeForm
    add_form = CustomUserCreationForm
    prepopulated_fields = {"slug": ("name", "surname", "random_identifier")}
    list_display = ("email", "date_of_birth", "is_admin", "id", "random_identifier")
    list_filter = ("is_admin",)
    fieldsets = (
        (
            None,
            {"fields": ("email", "password", "slug", "name", "surname", "random_identifier")},
        ),
        ("Personal info", {"fields": ("date_of_birth", "city")}),
        ("Permissions", {"fields": ("is_admin", "groups", "is_active", "is_superuser", "user_permissions")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "date_of_birth",
                    "password1",
                    "password2",
                    "name",
                    "surname",
                    "slug",
                    "random_identifier",
                ),
            },
        ),
    )
    ordering = ("-id",)


admin.site.register(MyCustomUser, UserAdmin)
