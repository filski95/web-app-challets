from accounts.models import MyCustomUser
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Q
from rest_framework import generics, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response

from .models import CustomerProfile, Opinion, Suggestion
from .permissions import IsAuthorOrAdmin, IsAuthorOtherwiseViewOnly
from .serializers import CustomerProfileSerializer, OpinionSerializer, SuggestionSerializer


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

    queryset = Opinion.objects.all()
