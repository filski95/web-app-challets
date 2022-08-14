from django.shortcuts import render
from django.urls import reverse_lazy
from django.views import generic

from accounts.forms import CustomUserCreationForm


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("accounts:login")
    template_name = "registration/signup.html"
