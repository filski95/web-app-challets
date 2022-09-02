import datetime
import io
import os
from datetime import date
from unittest import mock

from accounts.models import MyCustomUser
from django.test import TestCase
from django.urls import reverse
from PIL import Image
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.test import APITestCase

from bookings.models import ChalletHouse, Opinion, Reservation, Suggestion
from bookings.utils import my_date


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
        self.assertEqual(
            str(profile),
            f"Profile of: {str(profile.user).title()} [ID: {profile.user.id}]; joined on {profile.joined}",
        )

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
        #! must replicate the actual sentinel user used in foreign key as default
        cls.sentinel_user = MyCustomUser.objects.create(
            email="sentinel_user@gmail.com",
            name="Anonimowy",
            surname="Uzytkownik",
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
        self.assertEqual(new_suggestion.author.name, "Anonimowy")

    def test_suggestion_list_create_view_testuser(self):
        """authenticate user should see only his suggestions"""
        url = reverse("bookings:suggestions")
        self.client.force_authenticate(self.testuser)

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, [self.suggestion1.title, self.testuser.full_name])
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
                self.sentinel_user.full_name,  # anonymous user implementation
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
        self.assertContainsAll(response, [self.opinion.main_text, "author"])

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


class CustomerChalletHousesAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.testuser = MyCustomUser.objects.create_user(
            email="test@gmail.com",
            name="testname",
            surname="testsurname",
            date_of_birth=date(1995, 10, 10),
            password="adminadmin1",
        )

        cls.testuser2 = MyCustomUser.objects.create_user(
            email="test2@gmail.com",
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
        #! must replicate the actual sentinel user used in foreign key as default
        cls.sentinel_user = MyCustomUser.objects.create(
            email="sentinel_user@gmail.com",
            name="Anonimowy",
            surname="Uzytkownik",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )
        cls.house_nb_1 = ChalletHouse.objects.create(price_night=350, house_number=1)

        cls.first_reservation = Reservation.objects.create(
            customer_profile=cls.testuser.customerprofile,
            reservation_owner=cls.testuser,
            house=cls.house_nb_1,
            start_date=date(2022, 10, 10),
            end_date=date(2022, 10, 15),
        )

        #! this seservation is meant to have the latest date should there be any more added later
        cls.last_reservation = Reservation.objects.create(
            customer_profile=cls.testuser2.customerprofile,
            reservation_owner=cls.testuser2,
            house=cls.house_nb_1,
            start_date=date(2022, 11, 10),
            end_date=date(2022, 11, 15),
        )

    def return_all_nights(self, reservations=None):
        if reservations is None:
            reservations = Reservation.objects.all()
        night_counter = 0
        for r in reservations:
            night_counter += r.nights

        return night_counter

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

    def assertNotContainsAll(self, response, texts, status_code=200, msg_prefix="", html=False):
        """assert that none of the inputs is in the response's content"""
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
        self.assertTrue(total_count == 0)

    def test_challet_house_list_view(self):
        """list view -> allow any only get allowed. Test written assuming there are 2 reservations"""

        url = reverse("bookings:challet_houses")
        response = self.client.get(url)
        # response.data = [ordered_dict ... (house_nb : already_reserved_nights: [dates])]
        dates_str = [str(d) for d in response.data[0].get("already_reserved_nights").get(self.house_nb_1.house_number)]
        reservation = self.first_reservation
        content_list = [str(self.testuser.customerprofile), reservation.start_date, reservation.end_date]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, content_list)
        all_nights = self.return_all_nights() + 2
        self.assertEqual(len(dates_str), all_nights)
        self.assertEqual(dates_str[0], str(reservation.start_date))
        self.assertEqual(dates_str[-1], str(self.last_reservation.end_date))
        self.assertEqual(reservation.total_price, reservation.nights * self.house_nb_1.price_night)

        response_post = self.client.post(url, data={"price_night": 350, "house_number": 2})
        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response_put = self.client.put(url, data={"price_night": 350, "house_number": 1})
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_challet_house_detail_view(self):
        """Test written assuming there are 2 reservations"""
        url = reverse("bookings:challet_house", kwargs={"pk": self.house_nb_1.house_number})

        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        response = self.client.get(url)

        # response data = {..already_reserved_nights: house_nb: dates.... 'house_reservations':Ordered_Dict ->}
        dates_str = [str(d) for d in response.data.get("already_reserved_nights").get(self.house_nb_1.house_number)]

        # print(response.data.get("already_reserved_nights").get(self.house_nb_1.house_number))
        reservation = self.first_reservation
        content_list = [str(self.testuser.customerprofile), reservation.start_date, reservation.end_date]

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, content_list)
        all_nights = self.return_all_nights() + 2
        self.assertEqual(len(dates_str), all_nights)
        self.assertEqual(dates_str[0], str(reservation.start_date))
        self.assertEqual(dates_str[-1], str(self.last_reservation.end_date))
        self.assertEqual(reservation.total_price, reservation.nights * self.house_nb_1.price_night)

        response_post = self.client.post(url, data={"price_night": 350, "house_number": 2})
        self.assertEqual(response_post.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response_put = self.client.put(url, data={"price_night": 350, "house_number": 1})
        self.assertEqual(response_put.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        # lists house reservations properly
        self.assertEqual(len(response.data.get("house_reservations")), Reservation.objects.count())

    def test_reservation_create_view(self):

        data = {"start_date": date(2022, 10, 11), "end_date": date(2022, 12, 23), "house": 1}
        url = reverse("bookings:reservation_create")

        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # with self.raises did not work for the serialzier exception..
        self.client.force_authenticate(self.testuser)
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_406_NOT_ACCEPTABLE)
        self.assertEqual(response.data.get("detail")[:16], "There is already")  # msg from exception

        # wrong dates - end date before start date / validation ok
        data = {"end_date": date(2022, 10, 11), "start_date": date(2022, 12, 23), "house": 1}
        response = self.client.post(url, data=data)

        stream = io.BytesIO(response.content)
        parsed_data = JSONParser().parse(stream)
        self.assertEqual(parsed_data.get("non_field_errors")[0], "End date must be later than start date")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {"start_date": date(2022, 12, 20), "end_date": date(2022, 12, 23), "house": 1}
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        new_reservation = Reservation.objects.all().last()
        self.assertEqual(new_reservation.start_date, data.get("start_date"))
        self.assertEqual(new_reservation.status, 0)  # default status 0 -> not confirmed
        self.assertEqual(new_reservation.end_date, data.get("end_date"))
        self.assertEqual(new_reservation.house.house_number, data.get("house"))

    def test_reservation_list_view(self):
        """
        reservation list requires users to be logged in and adjusts the content:
        - users can see only their reservations, - admins all reservations
        - unsafe methods not allowed (no creation)
        """
        # not authenticated request
        url = reverse("bookings:reservations")
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        # only users reservation
        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, str(self.testuser.customerprofile))
        self.assertNotContains(response, str(self.testuser2.customerprofile))
        self.client.logout()
        # admin sees all
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, str(self.testuser.customerprofile))
        self.assertContains(response, str(self.testuser2.customerprofile))
        self.assertEqual(len(response.data), Reservation.objects.count())
        self.assertContains(response, "reservation_url")
        self.assertNotContainsAll(response, ["created_at", "updated_at", "id", "reservation_owner"])

    def test_reservation_detail_view(self):
        """
        user can only see his reservation's detail view, admins can see all..
        -> get and put methods allowed. The only writable field is status, the rest is view only
        -> displays more fields than list view
        """
        # must be logged in
        url = reverse("bookings:reservation_detail", kwargs={"pk": self.first_reservation.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # random user wont see sb's reservation detail view
        self.client.force_authenticate(self.testuser2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.client.logout()

        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, ["created_at", "updated_at", "reservation_owner"])
        self.assertNotContains(response, "id")  # dont want to display id ->res num enough
        self.client.logout()

        # admin can see testuser's
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, ["created_at", "updated_at", "reservation_owner"])
        self.assertNotContains(response, "id")  # dont want to display id ->res num enough
        # admin can see testuser2's
        url2 = reverse("bookings:reservation_detail", kwargs={"pk": self.last_reservation.id})
        response = self.client.get(url2)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, ["created_at", "updated_at", "reservation_owner"])
        self.assertNotContains(response, "id")  # dont want to display id ->reserv. num enough

    def test_reservation_detail_changing_statuses(self):
        """
        reservations are by default not confirmed [0]. After a reservation has been confirmed its status changes to [1]
        -> once confirmed reservation cannot be set to "not confirmed" again. The only option remaininig is to cancel it entirely
        -> cancellation cannot be reverted -> new reservation must be created if needed
        -> after cancellation, date attributes become Nones, nights are 0 and total_value is 0
        """
        url = reverse("bookings:reservation_detail", kwargs={"pk": self.first_reservation.id})
        self.client.force_authenticate(self.testuser)

        # 0 - not confirmed -> default setting after creation
        self.assertEqual(self.first_reservation.status, 0)

        data = {"status": 1}  # confirming reservation
        response = self.client.put(url, data=data)
        self.first_reservation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.first_reservation.status, 1)

        data = {"status": 0}  # trying to set confirmed reser. to "not confirmed"
        response = self.client.put(url, data=data)
        self.first_reservation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {"status": 9}
        response = self.client.put(url, data=data)
        self.first_reservation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.first_reservation.status, 9)
        self.assertEqual(self.first_reservation.start_date, None)
        self.assertEqual(self.first_reservation.end_date, None)
        self.assertEqual(self.first_reservation.nights, 0)
        self.assertEqual(self.first_reservation.total_price, 0)

        data = {"status": 0}  # trying to set cancelled reser. to "not confirmed"
        response = self.client.put(url, data=data)
        self.first_reservation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        data = {"status": 1}  # trying to set cancelled reser. to "confirmed"
        response = self.client.put(url, data=data)
        self.first_reservation.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.first_reservation.refresh_from_db()
        list_view_url = reverse("bookings:reservations")
        response = self.client.get(list_view_url)
        self.assertNotContainsAll(
            response,
            [
                self.first_reservation.reservation_number,
                f"http://0.0.0.0:8000/bookings/reservations/{self.first_reservation.id}/",
            ],
        )

    @mock.patch("bookings.utils.my_date.today")
    def test_validate_future_date_past_reservation_list_records(self, d):
        """
        changing the return of my_date.today() to a date past reservations
        admin should see all of them
        """
        my_date.today.return_value = date(2022, 12, 25)
        url = reverse("bookings:past_reservations")
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(url)

        self.assertEqual(len(response.data), Reservation.objects.count())
        self.client.logout()

        # user sees only his past reservations
        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(len(response.data), len(Reservation.objects.filter(reservation_owner=self.testuser)))
