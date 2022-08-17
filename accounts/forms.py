from django.contrib.auth.forms import UserChangeForm, UserCreationForm

from .models import MyCustomUser


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = MyCustomUser
        fields = ("email", "name", "surname", "id")


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = MyCustomUser
        fields = "__all__"
