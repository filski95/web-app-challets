import io
import os
from datetime import date

from accounts.models import MyCustomUser
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import serializers, status
from rest_framework.test import APITestCase

from bookings.models import Opinion, Suggestion
from bookings.serializers import OpinionSerializer


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
        cls.sentinel_user = MyCustomUser.objects.create(
            email="sentinel_user@gmail.com",
            name="Anonymous",
            surname="admins",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )

        cls.suggestion1 = Suggestion.objects.create(
            title="test suggestion",
            main_text="nice suggestion",
            author=cls.testuser,
        )
        cls.suggestion2 = Suggestion.objects.create(
            title="test suggestion2",
            main_text="nice suggestion2",
            author=cls.sentinel_user,
        )

        cls.opinion = Opinion.objects.create(
            title="test suggestion",
            main_text="nice suggestion",
            author=cls.testuser,
        )
        cls.anonymous_opinion = Opinion.objects.create(
            title="test anonymous suggestion",
            main_text="nice anonymous suggestion",
            name=cls.testuser.name,
            surname=cls.testuser.surname,
        )

    def generate_photo_file(self):
        file = io.BytesIO()
        image = Image.new("RGBA", size=(100, 100), color=(155, 0, 0))
        image.save(file, "png")
        file.name = "test.png"
        file.seek(0)
        return file

    def clean_foto(self, image):
        path = "media/" + image.name
        os.remove(path)

    def assertContainsAll(self, response, texts, status_code=200, msg_prefix="", html=False):
        """assert contains for multiple values"""
        total_count = 0
        loops = 0
        for text in texts:
            text_repr, real_count, msg_prefix = self._assert_contains(response, text, status_code, msg_prefix, html)
            if real_count:
                # disregarding number of found items, just add 1 if sth found
                total_count += 1
            # add each loop
            loops += 1
        # if all "texts" were found then loops and total_count are the same
        # otherwise at least 1 item was not found
        self.assertTrue(total_count == loops)

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

    def test_suggestion_list_create_view_anonymous(self):
        """annonymous user can send suggestions -> sentinel user attached to the suggestion obj."""

        url = reverse("bookings:suggestions")

        # should be empty list
        response_get = self.client.get(url)

        self.assertEqual(response_get.status_code, status.HTTP_200_OK)
        self.assertContains(response_get, [])

        suggestion3 = {"title": "suggestion3", "main_text": "nice suggestion3"}
        response = self.client.post(url, data=suggestion3)
        new_suggestion = Suggestion.objects.get(title="suggestion3")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(new_suggestion.author.name, "Anonymous")

    def test_suggestion_list_create_view_testuser(self):
        """authenticate user should see only his suggestions"""
        url = reverse("bookings:suggestions")
        self.client.force_authenticate(self.testuser)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.suggestion1.title)
        self.assertNotContains(response, self.suggestion2.title)

        test_photo = self.generate_photo_file()
        suggestion = {"title": "suggestion", "main_text": "nice suggestion", "image": test_photo}

        response_post = self.client.post(url, data=suggestion)
        self.clean_foto(test_photo)
        self.assertEqual(response_post.status_code, status.HTTP_201_CREATED)

    def test_suggestion_detail_view(self):

        url = reverse("bookings:suggestion_detail", kwargs={"pk": self.suggestion1.pk})
        # get anonymous
        response_anonymous = self.client.get(url)
        self.assertEqual(response_anonymous.status_code, status.HTTP_401_UNAUTHORIZED)

        # get author of the suggestion
        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        s = self.suggestion1
        self.assertContainsAll(response, [s.title, s.main_text, "author"])

        # put author of the suggestion
        test_photo = self.generate_photo_file()
        response_put = self.client.put(
            url, data={"title": "changed title", "main_text": "nice suggestion", "image": test_photo}
        )
        self.assertEqual(response_put.status_code, status.HTTP_200_OK)
        self.assertContains(response_put, "changed title")
        self.clean_foto(test_photo)

    def test_suggestion_detail_view_admin(self):
        url = reverse("bookings:suggestion_detail", kwargs={"pk": self.suggestion1.pk})
        test_photo = self.generate_photo_file()

        self.client.force_authenticate(self.admin_user)
        response_admin = self.client.get(url)
        self.assertEqual(response_admin.status_code, status.HTTP_200_OK)
        # admin can also make changes in suggestions..
        r_admin_put = self.client.put(url, data={"title": "admin", "main_text": "nice ", "image": test_photo})
        self.assertEqual(r_admin_put.status_code, status.HTTP_200_OK)
        self.assertContainsAll(r_admin_put, ["admin", "nice"])
        self.clean_foto(test_photo)

    def test_opinion_list_create_view_testuser(self):
        """any user (authenticated or not) can see opinions"""
        url = reverse("bookings:opinions")

        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(
            response,
            [
                self.opinion.title,
                self.opinion.main_text,
                self.anonymous_opinion.title,
                self.anonymous_opinion.main_text,
            ],
        )

        # anonymous user must provide name and surname
        data = {"title": "test anonymous suggestion", "main_text": "nice anonymous suggestion"}
        with self.assertRaises(TypeError):
            error_response = self.client.post(url, data=data)

        # anonymous user have to provide real data that was already used in user registration
        # TODO to implement -> only names/surnames of past clients
        data2 = {
            "title": "test anonymous suggestion",
            "main_text": "nice anonymous suggestion",
            "name": "madeupname",
            "surname": "madeupsurname",
        }
        with self.assertRaises(Opinion.DoesNotExist):
            error_response = self.client.post(url, data=data2)

        # correct creation of an Opinion
        # TODO in the future the check needs to be against past clients, not users in general
        # TODO atm creation of user -> fake details -> fake opinion
        data3 = {
            "title": "test anonymous suggestion",
            "main_text": "nice anonymous suggestion",
            "name": self.testuser.name,
            "surname": self.testuser.surname,
        }

        new_opinion = Opinion.objects.all().last()

        response = self.client.post(url, data=data3)
        self.assertEqual(new_opinion.title, data3.get("title"))
        self.assertEqual(new_opinion.main_text, data3.get("main_text"))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_opinion_detail_view(self):
        """
        - all users (authenticated or not) can view certain opinion
        - admins cannot change them
        - authors can change them
        """
        url = reverse("bookings:opinion_detail", kwargs={"pk": self.opinion.id})

        # all users can see opinions/ even not authenticated ones
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, self.opinion.main_text)

        # admins not allowed to change opinions
        self.client.force_authenticate(self.admin_user)
        data = {"title": "admin_title", "main_text": "admin main text"}
        url = reverse("bookings:opinion_detail", kwargs={"pk": self.opinion.id})
        response = self.client.put(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

        # opinion author can amend it
        self.client.force_authenticate(self.testuser)
        data = {"title": "title", "main_text": "main text"}
        response = self.client.put(url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
