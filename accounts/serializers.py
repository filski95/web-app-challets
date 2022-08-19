import re
from datetime import date

from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import MyCustomUser, create_random_identifier


class MyCustomUserSerializer(serializers.Serializer):

    email = serializers.EmailField(max_length=40, validators=[UniqueValidator(queryset=MyCustomUser.objects.all())])
    name = serializers.CharField(max_length=20)
    surname = serializers.CharField(max_length=20)
    date_of_birth = serializers.DateField()
    city = serializers.CharField(max_length=25, required=False)
    password = serializers.CharField(write_only=True, required=True)
    password2 = serializers.CharField(write_only=True, required=True)
    random_identifier = serializers.IntegerField(default=create_random_identifier, read_only=True)
    customerprofile = serializers.HyperlinkedRelatedField(read_only=True, view_name="bookings:single_customer")
    url = serializers.HyperlinkedIdentityField(read_only=True, view_name="accounts:user_detail", lookup_field="slug")

    class Meta:
        # very unlikely to happen
        # combination of these fields is used as a slug in url
        # encouraging the user to create account with the same data in few mins
        # random identifeir will change then
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=MyCustomUser.objects.all(),
                fields=["name", "surname", "random_identifier"],
                message="Please try again in few mins",
            )
        ]

    def get_fields(self, *args, **kwargs):
        """
        - customerprofile field to be visible only for users with admin status.
        """
        fields = super().get_fields(*args, **kwargs)
        # context = {'request': <rest_framework.request.Request: GET '/accounts/users/askdaskd-askdaskda-396'>}
        request = self.context.get("request")

        if isinstance(request.user, AnonymousUser) or request.user.is_admin is False:
            fields.pop("customerprofile")
        return fields

    def create(self, validated_data):

        if validated_data.get("admin"):
            # delete the argument passed into save in AdminUserList Post
            # as it would crash the program -> Non existent on MyCustomUser.
            # used only to trigger create_superuser
            validated_data.pop("admin")
            return MyCustomUser.objects.create_superuser(**validated_data)
        return MyCustomUser.objects.create_user(**validated_data)

    def update(self, instance, validated_data):

        instance.email = validated_data.get("email", instance.email)
        instance.name = validated_data.get("name", instance.name)
        instance.surname = validated_data.get("surname", instance.surname)
        instance.date_of_birth = validated_data.get("date_of_birth", instance.date_of_birth)
        instance.city = validated_data.get("city", instance.city)
        password = validated_data.get("password")
        if password:
            # must be hashed, otherwise will be stored as plain text and wont allow logins
            instance.set_password(password)

        instance.save()
        return instance

    #! validators

    def validate_date_of_birth(self, value):
        if date.today().year - value.year < 16:
            raise serializers.ValidationError("User must be older than 16 years old")
        return value

    def validate(self, data):
        """
        - check password, password2
        - do not allow the same inputs in name and surname fields
        - skipped for partial updates where no name/surname is altered (parial=True -> self.partial)
        - in case name or surname is mentioned we make a comparison by (in case only 1 field was supplied)
        looking up the missing value by filtering on the object(user) id provided in the context to a serializer
        in a patch method
        """

        data = self._password_checker(data)
        # user creation/full update
        if not self.partial:
            if data.get("name") == data.get("surname"):
                raise serializers.ValidationError("Check you name and surname! These cannot be identical")
            return data

        # partial update
        if self.partial and not (data.get("name") or data.get("surname")):
            return data

        # names must be != surname.
        changed_user = MyCustomUser.objects.get(id=self.context.get("obj"))
        if data.get("name", changed_user.name).lower() == data.get("surname", changed_user.surname).lower():
            raise serializers.ValidationError("Check you name and surname! These cannot be identical")

        return data

    def _password_checker(self, data):
        """
        - compares password and password2, checks if password is in line with requirements.
        - raises DRF validation error in case of error
        - removes password2 before returning the data dictionary as it is redundant later.
        """

        password = data.get("password")
        password2 = data.get("password2")

        # partial update no password
        if not (password and password):
            return data

        # creation / password involved password must have at least one letter nb and 8 chars
        elif password != password2 or not re.search(r"(?=.*[A-Za-z])(?=.*\d)(\w{8,}\d)", password):
            raise serializers.ValidationError(
                "Passwords must match, have at least 8 characters at least 1 number and letter"
            )

        # if everything ok, remove password2 -> no such argument in creation methods
        data.pop("password2")

        return data
