import random
from datetime import date

from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from .models import MyCustomUser, create_random_identifier


class MyCustomUserSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=40, validators=[UniqueValidator(queryset=MyCustomUser.objects.all())])
    name = serializers.CharField(max_length=20)
    surname = serializers.CharField(max_length=20)
    date_of_birth = serializers.DateField()
    city = serializers.CharField(
        max_length=25,
        required=False,
    )
    random_identifier = serializers.IntegerField(default=create_random_identifier, read_only=True)

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

    def create(self, validated_data):

        if validated_data.get("admin"):
            # delete the argument passed into save in AdminUserList Post
            # as it would crash the program -> Non existent on MyCustomUser.
            # used only to trigger create_superuser
            validated_data.pop("admin")
            return MyCustomUser.objects.create_superuser(**validated_data)
        return MyCustomUser.objects.create(**validated_data)

    def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        instance.name = validated_data.get("name", instance.name)
        instance.surname = validated_data.get("surname", instance.surname)
        instance.date_of_birth = validated_data.get("date_of_birth", instance.date_of_birth)
        instance.city = validated_data.get("city", instance.city)

        instance.save()
        return instance

    #! validators

    def validate_date_of_birth(self, value):
        if date.today().year - value.year < 16:
            raise serializers.ValidationError("User must be older than 16 years old")
        return value

    def validate(self, data):
        """
        - do not allow the same inputs in name and surname fields
        - skipped for partial updates where no name/surname is altered (parial=True -> self.partial)
        - in case name or surname is mentioned we make a comparison by (in case only 1 field was supplied)
        looking up the missing value by filtering on the object(user) id provided in the context to a serializer
        in a patch method
        """

        if self.partial and not (data.get("name") or data.get("surname")):
            return data

        changed_user = MyCustomUser.objects.get(id=self.context)
        if data.get("name", changed_user.name).lower() == data.get("surname", changed_user.surname).lower():
            raise serializers.ValidationError("Check you name and surname! These cannot be identical")

        return data
