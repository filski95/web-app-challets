from django.urls import path
from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


@extend_schema(
    request=None,
    responses={
        200: OpenApiResponse(
            description="urls listed in Json", examples=[OpenApiExample(name="customers", value="url_to_customers")]
        )
    },
)
@api_view(["GET"])
@permission_classes([AllowAny])
def api_root(request, format=None):
    return Response(
        {
            "users": reverse("accounts:users_list", request=request, format=format),
            "admin_users": reverse("accounts:admin_list", request=request, format=format),
            "customers": reverse("bookings:customers", request=request, format=format),
            "suggestions": reverse("bookings:suggestions", request=request, format=format),
            "opinions": reverse("bookings:opinions", request=request, format=format),
            "challet_houses": reverse("bookings:challet_houses", request=request, format=format),
            "reservations": reverse("bookings:reservations", request=request, format=format),
            "past_reservations": reverse("bookings:past_reservations", request=request, format=format),
            "create_reservation": reverse("bookings:reservation_create", request=request, format=format),
            "registration": reverse("rest_register", request=request, format=format),
            "rest_password": reverse("password_reset", request=request, format=format),
            "run_updates": reverse("bookings:run_updates", request=request, format=format),
            "stats": reverse("bookings:stats", request=request, format=format),
        }
    )
