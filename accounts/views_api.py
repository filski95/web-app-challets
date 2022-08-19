from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import MyCustomUser
from .serializers import MyCustomUserSerializer


class UsersListCreate(APIView):
    """View to list all users in the system and creation of new ones."""

    serializer_class = MyCustomUserSerializer  # without it, browsable API displays basic form Content Type and Content

    def get_object(self):
        users = MyCustomUser.objects.exclude(is_admin=True).select_related("customerprofile")
        return users

    def get(self, request, format=None):

        users = self.get_object()
        serializer = MyCustomUserSerializer(users, many=True, context={"request": request})
        return Response(serializer.data)

    def post(self, request, format=None):

        data = request.data
        serializer = MyCustomUserSerializer(data=data, context={"request": request})

        if serializer.is_valid(raise_exception=True):
            serializer.save()

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        users = self.get_object()
        users.delete()  # delete all normal users.
        return Response("Users were successfully deleted!", status=status.HTTP_204_NO_CONTENT)


class AdminUsersList(APIView):
    """View to list all admin users in the system and create new ones."""

    serializer_class = MyCustomUserSerializer

    def get(self, request, format=None):
        admin_users = MyCustomUser.admins.all().select_related("customerprofile")
        serializer = MyCustomUserSerializer(admin_users, many=True, context={"request": request})

        return Response(serializer.data)

    def post(self, request, format=None):

        data = request.data
        serializer = MyCustomUserSerializer(data=data, context={"request": request})

        if serializer.is_valid(raise_exception=True):
            # passing argument so that it pops up in the "validated data" in serializer's create method
            serializer.save(admin=True)
            return Response(f"Admin user: {serializer.data.get('name')} created", status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, format=None):
        admin_users = MyCustomUser.admins.all()

        # app owner remains untouched
        admin_users_to_be_deleted = admin_users.exclude(Q(email__exact="fskibaa@gmail.com") | Q(name__iexact="Filip"))
        admin_users_to_be_deleted.delete()
        return Response("Admin Users were successfully deleted!", status=status.HTTP_200_OK)


class UserDetail(APIView):
    """detail view for all users, regardles if admin or not"""

    serializer_class = MyCustomUserSerializer

    def get(self, request, slug, format=None):
        try:
            name, surname, identifier = slug.split("-")  # slug name-surname-identifier
            user = MyCustomUser.objects.get(
                Q(name__iexact=name), Q(surname__iexact=surname), Q(random_identifier=int(identifier))
            )

        except ObjectDoesNotExist:
            return Response("wrong id, user non existent")

        serializer = MyCustomUserSerializer(user, context={"request": request})

        return Response(serializer.data)

    def delete(self, request, slug, format=None):
        try:
            name, surname, identifier = slug.split("-")  # slug name-surname-identifier
            user = MyCustomUser.objects.get(
                Q(name__iexact=name), Q(surname__iexact=surname), Q(random_identifier=int(identifier))
            )
        except ObjectDoesNotExist:
            return Response("wrong data, user non existent")

        user.delete()
        return Response(f"{name} {surname} {identifier} has been deleted", status=status.HTTP_204_NO_CONTENT)

    def patch(self, request, slug, format=None):
        """
        - allows partial update of a user.
        - obj mandatory to identify the user and compare changed values to existing ones
        for valuation purposes
        """
        obj = MyCustomUser.objects.get(random_identifier=slug.split("-")[-1])
        data = request.data
        serializer = MyCustomUserSerializer(obj, data=data, partial=True, context={"obj": obj.id, "request": request})

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "changes made"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)