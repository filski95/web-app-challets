from core_project import main_api_view
from django.urls import path

from . import views_api

app_name = "bookings"


urlpatterns = [
    path("", main_api_view.api_root),
    path("customers/", views_api.customer_profiles, name="customers"),
    path("customers/<int:pk>/", views_api.single_profile, name="single_customer"),
    path("suggestions/", views_api.SuggestionUserListCreateView.as_view(), name="suggestions"),
    path("suggestions/<int:pk>/", views_api.SuggestionUserDetailView.as_view(), name="suggestion_detail"),
    path("opinions/", views_api.OpinionCreateListView.as_view(), name="opinions"),
    path("opinions/<int:pk>/", views_api.OpinionUserDetailView.as_view(), name="opinion_detail"),
    path("challet_houses/", views_api.ChalletHouseListView.as_view(), name="challet_houses"),
    path("challet_houses/<int:pk>/", views_api.ChalletHouseDetailView.as_view(), name="challet_house"),
    path("reservations/", views_api.ReservationsListViewSet.as_view({"get": "list"}), name="reservations"),
    path(
        "reservations/past_reservations/",
        views_api.ReservationsListViewSet.as_view({"get": "past_reservations"}),
        name="past_reservations",
    ),
    path("reservations/<int:pk>/", views_api.ReservationRetrieveUpdate.as_view(), name="reservation_detail"),
    path("reservations/create/", views_api.ReservationCreateView.as_view(), name="reservation_create"),
]
