from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse


@api_view(["GET"])
def api_root(request, format=None):
    return Response(
        {
            "users": reverse("accounts:users_list", request=request, format=format),
            "admin_users": reverse("accounts:admin_list", request=request, format=format),
            "customers": reverse("bookings:customers", request=request, format=format),
        }
    )
