from core_project import main_api_view
from django.urls import path

from . import views_api

app_name = "bookings"

urlpatterns = [
    path("", main_api_view.api_root),
    path("customers/", views_api.customer_profiles, name="customers"),
    path("customers/<int:pk>", views_api.single_profile, name="single_customer"),
]
