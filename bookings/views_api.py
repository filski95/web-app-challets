import json
from datetime import date
from types import DynamicClassAttribute
from typing import TypeVar, Union

from accounts.models import MyCustomUser
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db import models
from django.db.models import Avg, Case, Count, F, Max, Q, Sum, Value, When
from django.db.models.functions import Cast, Concat, ExtractDay, ExtractMonth, Length, Round
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django_filters import rest_framework as filters
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    PolymorphicProxySerializer,
    extend_schema,
    inline_serializer,
)
from rest_framework import filters as rest_filters
from rest_framework import generics
from rest_framework import serializers as rest_serializers
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from bookings import auxiliary
from bookings.filters import HouseFilter, OpinionFilter, ReservationFilter, SuggestionFilter
from bookings.paginators import MyCustomCursorPaginator, MyCustomListOffsetPagination, MyCustomPageNumberPagination
from bookings.utils import my_date

from .models import ChalletHouse, CustomerProfile, Opinion, Reservation, ReservationConfrimation, Suggestion
from .permissions import IsAuthorOrAdmin, IsAuthorOtherwiseViewOnly, IsOwnerOrAdmin
from .serializers import (
    BasicReservationSerializer,
    ChalletHouseSerializer,
    CustomerProfileSerializer,
    DetailViewReservationSerializer,
    OpinionSerializer,
    ReservationSerializer,
    RunUpdatesSerializer,
    SuggestionSerializer,
)


@extend_schema(responses=CustomerProfileSerializer)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def customer_profiles(request):
    if request.method == "GET":

        # allow optional ordering by joined date. If not, default is id
        if request.query_params.get("ordering") in ["joined", "-joined", "+joined"]:
            all_customer_profilers = (
                CustomerProfile.objects.select_related("user")
                .prefetch_related("reservation_set")
                .order_by(request.query_params.get("ordering"))
            )
        else:
            all_customer_profilers = (
                CustomerProfile.objects.select_related("user").prefetch_related("reservation_set").order_by("id")
            )

        paginator = MyCustomPageNumberPagination()
        paginated_pages = paginator.paginate_queryset(all_customer_profilers, request)

        if paginated_pages is not None:
            # context added cuz of the hyperlinked related field
            serializer = CustomerProfileSerializer(paginated_pages, many=True, context={"request": request})
            return paginator.get_paginated_response(serializer.data)

        serializer = CustomerProfileSerializer(all_customer_profilers, many=True, context={"request": request})
        return Response(serializer.data, status.HTTP_200_OK)


@extend_schema(responses=CustomerProfileSerializer)
@api_view(["GET"])
@permission_classes([IsAdminUser])
def single_profile(request, pk):
    """
    customer profile contains data that is not particularly relevant for end user, hence AdminOnly.
    """
    if request.method == "GET":
        profile = CustomerProfile.objects.select_related("user").get(id=pk)

        serializer = CustomerProfileSerializer(profile, context={"request": request})

        return Response(serializer.data, status=status.HTTP_200_OK)


@extend_schema(
    request=RunUpdatesSerializer,
    responses=RunUpdatesSerializer,
    parameters=[
        OpenApiParameter(
            name="run_updates",
            description="Run updates?",
            default=False,
            required=False,
            type=bool,
        )
    ],
)
@api_view(["POST", "GET"])
@permission_classes([IsAdminUser])
def run_updates(request):

    if request.method == "POST":

        data_to_serialize = request.data
        serializer = RunUpdatesSerializer(data_to_serialize)

        if serializer.data.get("run_updates"):
            customer_hierarchy = CustomerProfile.hierarchy
            end_date = my_date.today()  # + timedelta(10)  #! optional, manual testing mostly
            all_current_reservations = (
                Reservation.objects.filter(end_date__lte=end_date)
                .exclude(status__in=[9, 99])
                .select_related("customer_profile")
            )

            auxiliary.update_reservation_customerprofile(
                all_current_reservations, customer_hierarchy, end_date=end_date
            )

        return Response(serializer.data, status=status.HTTP_200_OK)

    # mostly for the browsable api, other than that POST only would do
    if request.method == "GET":
        return Response({"run_updates": False}, status=status.HTTP_200_OK)


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
                queryset = model.objects.select_related("author").order_by("id")
            else:
                queryset = model.objects.filter(author=current_user).select_related("author").order_by("id")
        else:
            queryset = model.objects.select_related("author").order_by(
                "id"
            )  # Opinions are allowed to be seen by everyone
    except TypeError:  # AnonymousUser cannot see any suggestions, user only his
        return None
    return queryset


class SuggestionUserListCreateView(generics.ListCreateAPIView):

    # random people, passers by allowed to send suggestion
    permission_classes = (AllowAny,)
    serializer_class = SuggestionSerializer
    filter_backends = (rest_filters.SearchFilter, filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    search_fields = ["title", "author"]
    filterset_class = SuggestionFilter
    ordering_fields = ["edited_on"]
    ordering = ["edited_on"]
    pagination_class = MyCustomCursorPaginator

    def get_queryset(self):

        if getattr(self, "swagger_fake_view", False):  # drf-yasg comp
            return Suggestion.objects.none()
        queryset = figure_the_queryset_out(self.request, Suggestion, limit_list_view=True)
        return queryset

    def perform_create(self, serializer):
        if type(self.request.user) == AnonymousUser:
            serializer.save()
        else:
            serializer.save(author=self.request.user)


class SuggestionUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthorOrAdmin,)

    def get_queryset(self):

        queryset = figure_the_queryset_out(self.request, Suggestion, limit_list_view=False)

        return queryset

    serializer_class = SuggestionSerializer


class OpinionCreateListView(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = OpinionSerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = OpinionFilter
    ordering_fields = ["edited_on"]
    ordering = ["edited_on"]
    pagination_class = MyCustomCursorPaginator
    throttle_classes = [auxiliary.CustomUseRateThrottle]

    def get_queryset(self):

        queryset = figure_the_queryset_out(self.request, Opinion, limit_list_view=False)
        return queryset

    def perform_create(self, serializer):
        user = self.request.user

        if type(user) != AnonymousUser:
            serializer.save(author=user)
            return
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

        past_user = MyCustomUser.objects.filter(
            Q(name=name) & Q(surname=surname) & Q(customerprofile__total_visits__gt=0)
        )
        if len(past_user) < 1:
            raise Opinion.DoesNotExist(
                "I am sorry, We Did not find any customer who visited us with such name and surname"
            )

        return serializer


class OpinionUserDetailView(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthorOtherwiseViewOnly,)
    serializer_class = OpinionSerializer
    throttle_classes = [auxiliary.CustomUseRateThrottle]

    def get_queryset(self):

        queryset = figure_the_queryset_out(self.request, Opinion, limit_list_view=False)
        return queryset


class ChalletHouseListView(generics.ListAPIView):
    """
    limited overall number of houses - no creation possible.
    -> search by reservation_number enabled [res:house]
    -> custom filterset [filters.py]
    """

    permission_classes = (AllowAny,)
    serializer_class = ChalletHouseSerializer
    filter_backends = [filters.DjangoFilterBackend, rest_filters.OrderingFilter, rest_filters.SearchFilter]
    filterset_class = HouseFilter
    ordering_fields = ["house_number", "sum_nights", "num_reservations"]  # see annotate [get_queryset]
    search_fields = ["house_reservations__reservation_number"]
    pagination_class = MyCustomPageNumberPagination
    throttle_classes = [auxiliary.SustainedRateThrottle]

    def get_queryset(self):
        # order by added due to pagination.

        queryset = (
            ChalletHouse.objects.prefetch_related("house_reservations__customer_profile")
            .annotate(num_reservations=Count("house_reservations"), sum_nights=Sum("house_reservations__nights"))
            .order_by("house_number")
        )

        return queryset


class ChalletHouseDetailView(generics.RetrieveAPIView):
    permission_classes = (AllowAny,)
    serializer_class = ChalletHouseSerializer

    def get_queryset(self):

        queryset = ChalletHouse.objects.all()

        return queryset


@method_decorator(cache_page(3), name="dispatch")
class ReservationsListViewSet(viewsets.ModelViewSet):
    """
    viewset limited to listing reservations:
    1. bookings:reservations lists all current + future reservations for admins; and the same but for specific user for non admins
    2. bookings:past_reservations lists all past reservations for admins; all past reservations of a user for non admin users
    """

    permission_classes = (IsAuthenticated,)
    serializer_class = BasicReservationSerializer
    filter_backends = (filters.DjangoFilterBackend, rest_filters.OrderingFilter)
    filterset_class = ReservationFilter
    ordering_fields = ("reservation_number", "start_date")
    ordering = "start_date"
    pagination_class = MyCustomListOffsetPagination

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):  # drf-yasg comp
            return Reservation.objects.none()

        if self.request.user.is_admin is True:
            queryset = (
                Reservation.objects.filter(Q(end_date__gte=my_date.today()))
                .select_related("customer_profile__user")
                .order_by("house", "start_date")
            )
        else:
            queryset = (
                Reservation.objects.select_related("customer_profile__user")
                .filter(
                    Q(reservation_owner__id=self.request.user.id)
                    & ~Q(start_date=None)
                    & Q(end_date__gte=my_date.today())
                )
                .order_by("house", "start_date")
            )

        queryset = self.filter_queryset(queryset)

        return queryset

    @action(detail=False)
    def past_reservations(self, request, *args, **kwargs):
        past_reservations = Reservation.objects.all().select_related("customer_profile__user", "reservation_owner")

        if request.user.is_admin is True:

            past_reservations = [r for r in past_reservations if r.end_date is None or r.end_date < my_date.today()]
            serializer = self.get_serializer(past_reservations, many=True)

        # if not admin then limit output to user's reservations only.
        else:

            past_reservations = [
                r
                for r in past_reservations
                if (r.end_date is None or r.end_date < my_date.today()) and r.reservation_owner.id == request.user.id
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

    def get_serializer_class(self):

        # if admin then return a default serializer with complete option as well (status)

        try:
            if self.request.user.is_admin:
                return super().get_serializer_class()
        except AttributeError:
            pass

        # otherwise let the user only see 3 options -> complete option done automatically after stay
        CONFIRMED = 1
        NOT_CONFIRMED = 0
        CANCELLED = 9
        choices = (
            (CONFIRMED, "Reservation confirmed"),
            (NOT_CONFIRMED, "Reservation not confirmed"),
            (CANCELLED, "Reservation is cancelled"),
        )

        class TweakedDetailViewReservationSerializer(DetailViewReservationSerializer):
            status = rest_serializers.ChoiceField(choices=choices, source="get_status_display")

            class Meta:
                model = Reservation
                fields = "__all__"

        return TweakedDetailViewReservationSerializer

    # @extend_schema(
    #     responses={
    #         200: PolymorphicProxySerializer(
    #             component_name="Reservation",
    #             serializers=[DetailViewReservationSerializer, "TweakedDetailViewReservationSerializer"],
    #             resource_type_field_name="type",
    #         )
    #     }
    # )
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)


class ReservationCreateView(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = ReservationSerializer

    def get_queryset(self):
        queryset = Reservation.objects.all()
        return queryset

    def perform_create(self, serializer):
        serializer.save(reservation_owner=self.request.user, customer_profile=self.request.user.customerprofile)


class StatisticsView(APIView):

    permission_classes = (IsAdminUser,)

    @extend_schema(
        responses={200: inline_serializer("statistics_view", fields={"info": models.CharField()})},
        examples=[
            OpenApiExample(
                "Example 1",
                summary="list of all statistics for given 'category' -> json. ",
                description="4 categories in total: users, reservations, houses,opinions. By default all statistics are shown but optionally could be shrunk based on the url '?request_data'",
                value={
                    "challet_houses": {"total_reservations_house": [{"house_number": 1, "number_of_reservations": 50}]}
                },
                status_codes=[200],
            ),
        ],
    )
    def get(self, request, format=None):
        """
        main function of the view. Lets client choose statistics for one of the given models
        - if request_data is provided in the url, only respective statistics will be returned.
        - if request_data is not provided or is empty all statistics will be returned
        """
        url_params = request.query_params.get("request_data")
        # this dict  predetermined for clarity + it is passed to respective functions
        return_data = {"users": {}, "reservations": {}, "opinions": {}, "challet_houses": {}}

        list_of_functions = [
            {"users": self._prepare_user_statistics},
            {"opinions": self._prepare_opinions},
            {"reservations": self._prepare_reservations_statistics},
            {"challet_houses": self._prepare_challet_houses_statistics},
        ]

        list_index = 0
        for function in list_of_functions:
            # unpack dict_keys[key] -> key
            category_name = str(*function.keys())
            # None in case request_data is not in url. len(url_params)== 0 in case request_data is empty
            if url_params is None or category_name in url_params or len(url_params) == 0:
                # add the new category to the return_data dictionary. list_index increased with each loop, needed as functions are in a list
                return_data[category_name] = list_of_functions[list_index][category_name](return_data[category_name])
            list_index += 1

        return Response(return_data, status=status.HTTP_200_OK)

    def _prepare_user_statistics(self, return_data):

        # * get counts of user types: admin users and normal users
        user_types = MyCustomUser.objects.aggregate(
            admin=Count("pk", filter=Q(is_admin=True)), normal_user=Count("pk", filter=Q(is_admin=False))
        )
        return_data["user_types"] = user_types

        # * get month on which users registered. Basic query and then rest done on the python level
        customers = CustomerProfile.objects.all()
        months = {}

        for profile in customers:
            # get month name for all profiles on the joined field (January ..etc) and add + 1
            months[profile.joined.strftime("%B")] = months.get(profile.joined.strftime("%B"), 0) + 1
        return_data["joined_on_month"] = months

        # * calculate how many users belong to which category [New Customer, Regular, Super]
        hierarchies_count = CustomerProfile.objects.aggregate(
            new_customers=Count("status", filter=Q(status="N")),
            regular_customers=Count("status", filter=Q(status="R")),
            super=Count("status", filter=Q(status="S")),
        )
        return_data["customer_statuses"] = hierarchies_count

        # * list users ordered by the revenue generated by them.
        users = (
            CustomerProfile.objects.select_related("user")
            .annotate(generated_revenue=Sum(F("reservation__total_price")))
            .filter(~Q(generated_revenue=None))
            .order_by("-generated_revenue")
        )

        return_data["users_generated_revenue"] = {}
        for u in users:
            return_data["users_generated_revenue"].update({u.profile_user_repr: u.generated_revenue})

            # * return number of visits of each user in each house.
            customers_fav_houses = (
                # filter only reservstions with status completed => meaning past dates
                MyCustomUser.objects.filter(Q(reservations__status=99)).annotate(
                    house=F("reservations__house"),
                    # name + " " + surname + " [" + id + "]" -> Max Biaggi [1]
                    customer=Concat(
                        "name", Value(" "), "surname", Value(" ["), "pk", Value("]"), output_field=models.CharField()
                    ),
                )
                # group by custom and house
                .values_list("customer", "house")
                # count visits for each house id
                .annotate(total_visits=Count("reservations__house"))
                # sort by customer id
                .order_by("id")
            )

        return_data["favorite_houses"] = {}
        for data in customers_fav_houses:
            customer, house, total_visits = data

            if return_data["favorite_houses"].get(customer) is None:
                return_data["favorite_houses"][customer] = {}

            return_data["favorite_houses"][customer].update({house: {"total_visits": total_visits}})

        return return_data

    def _prepare_reservations_statistics(self, return_data):

        # * average lenght of the reservation / max_lenght of a reservation
        reservation_lengths = Reservation.objects.aggregate(
            stay_length=Avg(F("end_date") - F("start_date")), max_length=Max(F("end_date") - F("start_date"))
        )
        return_data["average_reservation_length"] = reservation_lengths["stay_length"].days
        return_data["max_length"] = reservation_lengths["max_length"].days

        # *return all users who has booked at least a night and provide count of their reservations [user : count of reservations]
        qs_reservations = (
            CustomerProfile.objects.annotate(reservations=Count("reservation"))
            .filter(reservations__gt=0)
            .select_related("user")
            .order_by("-reservations")
        )

        return_data["users_reservations"] = {}

        for i in qs_reservations:
            return_data["users_reservations"].update({i.profile_user_repr: i.reservations})

        # * users with their longest reservation
        longest_res = (
            CustomerProfile.objects.select_related("user")
            .annotate(max_length=F("reservation__end_date") - F("reservation__start_date"))
            .filter(~Q(max_length=None))
            .order_by("max_length")
            .distinct()
        )

        return_data["longest_reservation_per_user"] = {}

        for i in longest_res:
            return_data["longest_reservation_per_user"].update({i.profile_user_repr: i.max_length.days})

        # * gives count of cancelled, valid and total reservations
        users_reservations = CustomerProfile.objects.aggregate(
            cancelled_count=Count("reservation", filter=(Q(reservation__start_date=None))),
            not_cancelled_count=Count("reservation", filter=(~Q(reservation__start_date=None))),
            total=Count("reservation"),
        )

        return_data["total_reservations"] = users_reservations
        # * return count of the number of reservations with respective status
        reservations_status_split = Reservation.objects.aggregate(
            confirmed=Count("status", filter=Q(status=1)),
            not_confirmed=Count("status", filter=Q(status=0)),
            cancelled=Count("status", filter=Q(status=9)),
            completed=Count("status", filter=Q(status=99)),
        )
        return_data["reservations_statuses"] = reservations_status_split

        return_data["number_of_order_confirmations"] = ReservationConfrimation.objects.all().count()

        reservations = (
            Reservation.objects.filter(~Q(start_date=None))
            .annotate(months=ExtractMonth("start_date"))
            .values_list("months")
            .annotate(
                reservation_count=Count("id"),
                total_price=Sum("total_price"),
                average_stay=ExtractDay(Avg(F("end_date") - F("start_date"))),
                unique_customers=Count("customer_profile", distinct=True),
                max_length=Max("nights"),
            )
        ).order_by("months")

        return_data["reservations_monthly"] = {}

        for pair in reservations:
            month_number, count, revenue, avg_stay, unique_users, max_length = pair
            month = date(2020, month_number, 1).strftime("%B")
            return_data["reservations_monthly"].update(
                {
                    month: {
                        "count": count,
                        "monthly_revenue": revenue,
                        "average_stay_days": avg_stay,
                        "longest_stay": max_length,
                        "unique_customers": unique_users,
                    }
                }
            )

        return return_data

    def _prepare_opinions(self, return_data):
        # * computes basics stats: total number of opinions / frequency of images attached to opinions / longest_body

        opinions_details = (
            Opinion.objects.alias(img=Length("image"))
            # null for images did not work, if not provided it is "" in db apparently
            # if Length > 0 assign 1, if not, 0, and then aggregate average off of that.
            .annotate(
                img_binary=Case(
                    When(img=0, then=Value(0)),
                    When(img__gte=1, then=Value(1)),
                ),
                text_len=Length("main_text"),
            ).aggregate(
                number_of_opinions=Count("pk"),
                img_per_opinion=Round(Avg("img_binary"), precision=2),
                longest_body=Max("text_len"),
                avg_rating=Round(Avg("rating", filter=~Q(rating=None)), precision=2),
            )
        )

        return_data.update(opinions_details)

        # * gives stats to opinions based on the month they were created in
        opinions_per_month = (
            Opinion.objects.defer("main_text")
            .alias(img=Length("image"))
            .annotate(
                month=Cast(ExtractMonth("provided_on"), output_field=models.IntegerField()),
                img_binary=Case(
                    When(img=0, then=Value(0)),
                    When(img__gte=1, then=Value(1)),
                ),
            )
            .values_list("month")
            .annotate(count_month=Count(F("month")), image_per_month=Round(Avg("img_binary"), precision=2))
        )

        return_data["opinions_per_month"] = {}

        for data in opinions_per_month:
            month, counter, image_per_month = data
            month = date(2020, month, 1).strftime("%B")
            return_data["opinions_per_month"].update({month: {"count": counter, "image_per_opinion": image_per_month}})

        # * annotates pairs of  [concat(user.name,user.surname)]: number of opinions as "full_name" and groups results on that.
        # * computes number of opinions per user / average rating given by user
        user_opinions = (
            Opinion.objects.defer("main_text")
            .annotate(full_name=Concat("author__name", Value(" "), "author__surname"))
            .values_list("full_name")
            .annotate(nb_of_opinions=Count("pk"), avg_rating=Round(Avg("rating", filter=~Q(rating=None)), precision=2))
        ).order_by("-nb_of_opinions")

        return_data["user_opinions_count"] = {}
        for user_count in user_opinions:
            full_name, count, average_rating = user_count
            return_data["user_opinions_count"].update({full_name: {"count": count, "average_rating": average_rating}})

        return return_data

    def _prepare_challet_houses_statistics(self, return_data):

        # * return tuples of house_number, number of reservations
        total_reservations_house = (
            # group by house number
            ChalletHouse.objects.values("house_number")
            # to each house annotate count of reservations
            .annotate(number_of_reservations=Count("house_reservations")).order_by("house_number")
        )
        return_data["total_reservations_house"] = total_reservations_house

        # * return number of reservations per month for each of the houses
        opinions = (
            # "transform"/Extract from start_date month number-> month (number)
            ChalletHouse.objects.annotate(month=ExtractMonth("house_reservations__start_date"))
            # group by house number, month
            # based on that grouping count annnotate "c" as count of repetitions on each house number in given group
            .values_list("house_number", "month").annotate(c=Count("house_number"))
        ).order_by("house_number")

        return_data["reservations_per_house_monthly"] = {}

        for data in opinions:
            house_number, month, count = data
            if month is not None:
                month = date(2020, month, 1).strftime("%B")
            else:
                month = "Cancelled"

            if return_data["reservations_per_house_monthly"].get(house_number) is None:
                return_data["reservations_per_house_monthly"][house_number] = {}

            return_data["reservations_per_house_monthly"][house_number].update({month: {"reservations": count}})

        # * get total revenue generated by reservations of each house
        total_revenue_house = (
            # group by house number
            ChalletHouse.objects.values("house_number")
            # annotate to that the sum of reservations total_price
            .annotate(total_revenue=Sum("house_reservations__total_price")).order_by("house_number")
        )

        return_data["total_revenue_house"] = total_revenue_house

        return return_data
