from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class MyUserManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email or not name or not surname:
            raise ValueError("Users must have an email address, first name and last name")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            surname=surname,
            **extra_fields,
        )

        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(
            email,
            password=password,
            name=name,
            surname=surname,
            **extra_fields,
        )
        user.is_admin = True
        user.save()
        return user


class MyCustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(verbose_name="email address", max_length=40, unique=True)
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True, blank=True)  # not required at all
    city = models.CharField(max_length=25)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()

    USERNAME_FIELD = "email"  # email as main username

    REQUIRED_FIELDS = ["name", "surname"]  # admin createsuperuser

    def __str__(self) -> str:
        return f"User: {self.name} {self.surname}: {self.email}"

    @property
    def full_name(self):
        return f"{self.name} {self.surname}"
