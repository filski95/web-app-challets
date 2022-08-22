from datetime import date

from accounts.models import MyCustomUser
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class CustomerProfileTest(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.testuser = MyCustomUser.objects.create_user(
            email="test@gmail.com",
            name="testname",
            surname="testsurname",
            date_of_birth=date(1995, 10, 10),
            password="adminadmin1",
        )
        cls.admin_user = MyCustomUser.objects.create_superuser(
            email="admin@gmail.com",
            name="filip",
            surname="admins",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )

    def test_automatic_creation_customer_profile(self):
        creation_date = date.today()
        profile = self.testuser.customerprofile

        self.assertTrue(profile)
        self.assertEqual(profile.user, self.testuser)
        self.assertEqual(self.testuser.name, profile.first_name)
        self.assertEqual(self.testuser.surname, profile.surname)
        self.assertEqual(profile.joined, creation_date)
        self.assertEqual(profile.status, "N")
        self.assertEqual(profile.total_visits, 0)
        self.assertEqual(str(profile), f"Customer's profile of {profile.user} who joined on {profile.joined}")

    def test_automatic_update_customer_profile(self):

        self.testuser.name = "jan"
        self.testuser.surname = "kowalski"
        self.testuser.save()

        self.assertEqual(self.testuser.name, self.testuser.customerprofile.first_name)
        self.assertEqual(self.testuser.surname, self.testuser.customerprofile.surname)


class CustomerProfileAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.testuser = MyCustomUser.objects.create_user(
            email="test@gmail.com",
            name="testname",
            surname="testsurname",
            date_of_birth=date(1995, 10, 10),
            password="adminadmin1",
        )
        cls.admin_user = MyCustomUser.objects.create_superuser(
            email="admin@gmail.com",
            name="filip",
            surname="admins",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )

    def test_customers_view_admin_only(self):

        url = reverse("bookings:customers")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

        self.client.force_authenticate(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_customers_list_view_admin_only(self):

        url = reverse("bookings:single_customer", kwargs={"pk": self.testuser.customerprofile.id})

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

        self.client.force_authenticate(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
