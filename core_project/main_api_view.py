from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.reverse import reverse


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
            "registration": "/api/registration/",
        }
    )
