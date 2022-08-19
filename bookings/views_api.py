from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .models import CustomerProfile
from .serializers import CustomerProfileSerializer


@api_view(["GET"])
@permission_classes([IsAdminUser])
def customer_profiles(request):

    if request.method == "GET":
        all_customer_profilers = CustomerProfile.objects.all()

        # context added cuz of the hyperlinked related field
        serializer = CustomerProfileSerializer(all_customer_profilers, many=True, context={"request": request})

        return Response(serializer.data, status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def single_profile(request, pk):
    """
    customer profile contains data that is not particularly relevant for end user, hence AdminOnly.
    """
    if request.method == "GET":
        profile = CustomerProfile.objects.get(id=pk)

        serializer = CustomerProfileSerializer(profile, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)
