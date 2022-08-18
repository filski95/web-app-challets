import random

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse


def create_random_identifier():
    random_identifier = random.randint(1, 32766)
    return random_identifier


class AdminUserManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_admin=True)


class MyUserManager(BaseUserManager):
    def create_user(self, email, name, surname, password, **extra_fields):
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

    def create_superuser(self, email, name, surname, password, **extra_fields):
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
    """
    - Linked to the Customer profile model in bookings.
    """

    class Meta:
        verbose_name_plural = "Users"

    # to make slug less revealing (than ID) + could not make use of ID as there was no way to add it to the form (admin)
    random_identifier = models.SmallIntegerField(default=create_random_identifier, unique=True)
    email = models.EmailField(verbose_name="email address", max_length=40, unique=True)
    name = models.CharField(max_length=20)
    surname = models.CharField(max_length=20)
    date_of_birth = models.DateField(null=True)  # changed mid project.
    city = models.CharField(max_length=25, blank=True, null=True)
    slug = models.SlugField(max_length=200, unique=True, null=True)

    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)

    objects = MyUserManager()
    admins = AdminUserManager()

    USERNAME_FIELD = "email"  # email as main username
    REQUIRED_FIELDS = ["name", "surname"]  # admin createsuperuser

    def __str__(self) -> str:
        return f"User: {self.name} {self.surname}: {self.email}"

    @property
    def full_name(self):
        return f"{self.name} {self.surname}"

    def get_absolute_url(self):
        return reverse("accounts:user_detail", kwargs={"slug": self.slug})

    def save(self, *args, **kwargs):
        pre_slug = self.full_name + " " + str(self.random_identifier)
        # creating slug when new new user is created and updates the slug when existing user's name/surname are changed
        if not self.slug or pre_slug != self.slug:
            self.slug = slugify(pre_slug)

        return super().save(*args, **kwargs)
