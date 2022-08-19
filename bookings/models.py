from accounts.models import MyCustomUser
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


# class Reservation(models.Model):
#     reservation_owner = models.ForeignKey(CustomerProfile, on_delete=models.CASCADE)
