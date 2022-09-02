from datetime import timedelta
from time import time

from accounts.models import MyCustomUser
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q
from rest_framework import generics, status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from bookings.utils import my_date

from .models import ChalletHouse, CustomerProfile, Opinion, Reservation, Suggestion
from .permissions import IsAuthorOrAdmin, IsAuthorOtherwiseViewOnly, IsOwnerOrAdmin
from .serializers import (
    BasicReservationSerializer,
    ChalletHouseSerializer,
    CustomerProfileSerializer,
    DetailViewReservationSerializer,
    OpinionSerializer,
    ReservationSerializer,
    SuggestionSerializer,
)


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


def figure_the_queryset_out(request, model: models.Model, limit_list_view=False):
    """
    helper method used by Opinion and Suggestion serializers; logic differs as:
    - Suggestions can be sent by Anonymous users but they cannot view any other suggestions
    - Logged in users can send suggestions and view thier past ones; admin can see all
    - Opinions can be viewed by everyone [limit_list_view = False]

    """
    try:
        current_user = request.user
        if limit_list_view:
            if current_user.is_superuser == True:
                # admin can see an entire list with all suggestions
                queryset = model.objects.all()
            else:
                queryset = model.objects.filter(author=current_user)
        else:
            queryset = model.objects.all()  # Opinions are allowed to be seen by everyone
    except TypeError:  # AnonymousUser cannot see any suggestions, user only his
        return None
    return queryset


class SuggestionUserListCreateView(generics.ListCreateAPIView):

    # random people, passers by allowed to send suggestion
    permission_classes = (AllowAny,)
    serializer_class = SuggestionSerializer

    def get_queryset(self):
        queryset = figure_the_queryset_out(self.request, Suggestion, limit_list_view=True)
        return queryset

    def perform_create(self, serializer):
        if type(self.request.user) == AnonymousUser:
            serializer.save()
        else:

            serializer.save(author=self.request.user)


class SuggestionUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthorOrAdmin,)

    queryset = Suggestion.objects.all()
    serializer_class = SuggestionSerializer


class OpinionCreateListView(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = OpinionSerializer

    def get_queryset(self):

        queryset = figure_the_queryset_out(self.request, Opinion, limit_list_view=False)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if type(user) != AnonymousUser:

            serializer.save(author=user)
        else:
            serializer = self._check_if_anonymous_user_allowed_opinion(serializer)

        serializer.save()

    def _check_if_anonymous_user_allowed_opinion(self, serializer):
        """
        - not allowing people who never used facilities to place an opinion
        - in case of anonymous try, the user must provide name and surname which will be searched in the database of past users
        - method used in perform create which gets data from the serializer.data
        """
        name = self.request.data.get("name")
        surname = self.request.data.get("surname")

        if not (name and surname):
            raise TypeError("Anonymous users must provide name and surname")

        # TODO
        # TODO this needs to be amended to the user/customer profile with visits >= 1
        # TODO
        past_user = MyCustomUser.objects.filter(Q(name=name) & Q(surname=surname))
        if len(past_user) < 1:
            raise Opinion.DoesNotExist("I am sorry, We Did not find any customer with such name and surname")

        return serializer


class OpinionUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthorOtherwiseViewOnly,)
    serializer_class = OpinionSerializer

    def get_queryset(self):
        queryset = figure_the_queryset_out(self.request, Opinion, limit_list_view=False)
        return queryset


class ChalletHouseListView(generics.ListAPIView):
    """
    limited overall number of houses - no creation possible.
    """

    permission_classes = (AllowAny,)
    serializer_class = ChalletHouseSerializer

    def get_queryset(self):
        queryset = ChalletHouse.objects.prefetch_related("house_reservations__customer_profile").prefetch_related(
            "house_reservations__reservation_owner"
        )

        return queryset


class ChalletHouseDetailView(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ChalletHouseSerializer

    def get_queryset(self):
        queryset = ChalletHouse.objects.prefetch_related("house_reservations__customer_profile").all()
        return queryset


class ReservationsListViewSet(viewsets.ModelViewSet):
    """
    viewset limited to listing reservations:
    1. bookings:reservations lists all current + future reservations for admins; and the same but for specific user for non admins
    2. bookings:past_reservations lists all past reservations for admins; all past reservations of a user for non admin users
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = BasicReservationSerializer

    def get_queryset(self):

        if self.request.user.is_admin is True:
            queryset = Reservation.objects.filter(Q(end_date__gte=my_date.today())).order_by("house", "start_date")
        else:
            queryset = Reservation.objects.filter(
                Q(reservation_owner__id=self.request.user.id) & ~Q(start_date=None) & Q(end_date__gte=my_date.today())
            ).order_by("house", "start_date")
        return queryset

    @action(detail=False)
    def past_reservations(self, request, *args, **kwargs):
        past_reservations = Reservation.objects.all().select_related("customer_profile")

        if request.user.is_admin is True:

            past_reservations = [r for r in past_reservations if r.end_date < my_date.today()]
            serializer = self.get_serializer(past_reservations, many=True)

        else:
            past_reservations = [
                r
                for r in past_reservations
                if r.end_date < my_date.today() and r.reservation_owner.id == request.user.id
            ]
            serializer = self.get_serializer(past_reservations, many=True)

        return Response(serializer.data)


class ReservationRetrieveUpdate(generics.RetrieveUpdateAPIView):
    permission_classes = (IsOwnerOrAdmin,)
    serializer_class = DetailViewReservationSerializer
    http_method_names = ["get", "put"]

    def get_queryset(self):
        queryset = Reservation.objects.all()
        return queryset

    def perform_update(self, serializer):
        obj = self.get_object()

        serializer.save(obj=obj)


class ReservationCreateView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReservationSerializer

    def get_queryset(self):
        queryset = Reservation.objects.all()
        return queryset

    def perform_create(self, serializer):
        serializer.save(reservation_owner=self.request.user, customer_profile=self.request.user.customerprofile)
