import itertools
from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.reverse import reverse
from rest_framework.test import APIRequestFactory, APITestCase

from .models import MyCustomUser
from .serializers import MyCustomUserSerializer
from .views_api import UsersListCreate


class MyCustomUserTest(TestCase):
    def assertContainsAny(self, response, texts, status_code=200, msg_prefix="", html=False):
        """assert contains for multiple values"""
        total_count = 0
        for text in texts:
            text_repr, real_count, msg_prefix = self._assert_contains(response, text, status_code, msg_prefix, html)
            total_count += real_count

        self.assertTrue(total_count != 0)

    def test_user_creation(self):

        testuser = MyCustomUser.objects.create_user(
            email="test@gmail.com", name="testname", surname="testsurname", password="adminadmin"
        )

        self.assertEqual(testuser.name, "testname")
        self.assertNotEqual(testuser.name, "lalal")
        self.assertTrue(testuser.is_active)
        self.assertFalse(testuser.is_superuser)
        self.assertFalse(testuser.is_staff)
        self.assertFalse(testuser.is_admin)
        # checking property output - > Name Surname
        self.assertEqual(testuser.full_name, "testname testsurname")

    def test_superuser_creation(self):

        testuser = MyCustomUser.objects.create_superuser(
            email="test@gmail.com", name="testname", surname="testsurname", password="admin"
        )

        self.assertEqual(testuser.name, "testname")
        self.assertNotEqual(testuser.name, "lalal")
        self.assertTrue(testuser.is_active)
        self.assertTrue(testuser.is_superuser)
        self.assertTrue(testuser.is_staff)
        self.assertTrue(testuser.is_admin)

    def test_super_user_extra_fields(self):
        testuser = get_user_model()  # alternative way

        with self.assertRaises(ValueError):
            testuser.objects.create_superuser(
                email="super@user.com",
                name="testname",
                surname="testsurname",
                password="foo",
                is_superuser=False,
            )


class MyCustomUserTestAPI(APITestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.serializer = MyCustomUserSerializer

        cls.testuser = MyCustomUser.objects.create_user(
            email="test@gmail.com",
            name="testname",
            surname="testsurname",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )

        cls.admin_user = MyCustomUser.objects.create_superuser(
            email="admin@gmail.com",
            name="filip",
            surname="admins",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )

        cls.dummy_user = MyCustomUser.objects.create_user(
            email="dummy@gmail.com",
            name="dummy_name",
            surname="dummy_surname",
            date_of_birth=date(1995, 10, 10),
            password="passwordtest123",
        )

    def assertContainsAny(self, response, texts, status_code=200, msg_prefix="", html=False):
        """assert contains for multiple values"""
        total_count = 0
        for text in texts:
            text_repr, real_count, msg_prefix = self._assert_contains(response, text, status_code, msg_prefix, html)
            total_count += real_count
        self.assertTrue(total_count != 0)

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

    def test_main_api_view_only_for_authenticated_users(self):

        url = "/api/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        self.client.force_authenticate(self.testuser)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_admin_users_list_view_admin_only_anonymous(self):

        url = reverse("accounts:admin_list")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(response.data.get("detail"), "Authentication credentials were not provided.")

    def test_user_detail_get_not_admin(self):
        self.client.force_authenticate(self.testuser)
        response = self.client.get(reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug}))
        user_outputed = MyCustomUser.objects.filter(name=self.testuser.name).values_list(
            "email", "surname", "name", "email", "date_of_birth", "slug"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, *user_outputed)
        self.assertNotContains(response, "customerprofile")  # admin only

    def test_user_detail_get_admin(self):
        self.client.force_authenticate(self.admin_user)

        response = self.client.get(reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug}))
        user_outputed = MyCustomUser.objects.filter(name=self.testuser.name).values_list(
            "email", "surname", "name", "email", "date_of_birth", "slug"
        )

        self.assertContains(response, "customerprofile")  # admin only

    def test_user_detail_delete(self):
        self.client.force_authenticate(self.testuser)
        response = self.client.delete(reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug}))
        u = self.testuser

        self.assertEqual(response.data, f"{u.name} {u.surname} {u.random_identifier} has been deleted")
        self.assertEqual(response.content, b"")

    def test_user_detail_patch_email(self):
        """email change - ok unless same email already taken"""
        self.client.force_authenticate(self.testuser)
        url = reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug})

        data = {"email": "change_test@gmail.com"}
        response = self.client.patch(url, data=data)
        # reload to see the update - without it the old one shows up
        self.testuser.refresh_from_db()
        self.assertEqual(self.testuser.email, data.get("email"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # duplicates not allowed:
        temp_user = MyCustomUser.objects.create_user(
            email="test@g.com", name="test", surname="tests", date_of_birth=date(1995, 10, 10), password="admin"
        )
        factory = APIRequestFactory()
        data_temp = {"email": temp_user.email}
        request = factory.patch(url, data=data_temp)
        view = UsersListCreate.as_view()
        response = view(request, slug=self.testuser.slug)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotEqual(self.testuser.email, data_temp.get("email"))

    def test_user_detail_patch_name_surname(self):
        """
        - name and surname cannot be the same
        - slug must be updated after a successful change
        """

        data = {"surname": "testname"}
        self.client.force_authenticate(self.testuser)
        response = self.client.patch(reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug}), data=data)

        self.testuser.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotEqual(self.testuser.surname, data.get("surname"))  # no change

        data = {"surname": "testsurname"}
        r_success = self.client.patch(reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug}), data=data)

        self.testuser.refresh_from_db()
        name, surname, identifier = self.testuser.slug.split("-")
        self.assertEqual(surname, data.get("surname"))  # slug updates after name/surname change

    def test_user_detail_change_password(self):
        self.client.force_authenticate(self.testuser)
        initial_password = self.testuser.password
        data = {"password": "adminadmin123", "password2": "adminadmin123"}  # nb + letter + 8 char
        data_wrong = {"password": "adminadmin", "password2": "adminadmin"}  # lack of nb
        data_one_password = {"password": "adminadmin1"}  # only 1 password

        url = reverse("accounts:user_detail", kwargs={"slug": self.testuser.slug})

        response_data = self.client.patch(url, data=data)
        self.testuser.refresh_from_db()
        changed_password = self.testuser.password

        response_data_wrong = self.client.patch(url, data=data_wrong)
        self.testuser.refresh_from_db()
        error_msg = str(response_data_wrong.data.get("non_field_errors")[0])

        password_not_changed_error = self.testuser.password

        response_data_one_password = self.client.patch(url, data=data_one_password)

        self.assertEqual(response_data.status_code, status.HTTP_200_OK)
        self.assertNotEqual(initial_password, changed_password)
        self.assertContains(response_data, "changes made")
        self.assertEqual(response_data_wrong.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(changed_password, password_not_changed_error)
        self.assertEqual(error_msg, "Passwords must match, have at least 8 characters at least 1 number and letter")
        self.assertEqual(response_data_one_password.status_code, status.HTTP_400_BAD_REQUEST)

    def test_deatil_wont_work_with_somboedys_user_account(self):
        """
        detail view wont let users change other user's details
        """
        self.client.force_authenticate(self.testuser)
        data = {"name": "changed_name"}
        url = reverse("accounts:user_detail", kwargs={"slug": self.dummy_user.slug})

        response = self.client.patch(url, data)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_users_list_post_get_delete(self):
        self.client.force_authenticate(self.admin_user)
        data = {
            "name": "filip",
            "surname": "test",
            "email": "f@gmail.com",
            "date_of_birth": "1995-12-12",
            "city": "sosnowiec",
            "password": "admin1234123",
            "password2": "admin1234123",
        }
        # testing post / user creation
        response = self.client.post(reverse("accounts:users_list"), data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # testing get / list of users
        get_response = self.client.get(reverse("accounts:users_list"))
        self.assertEqual(get_response.status_code, status.HTTP_200_OK)
        self.assertContainsAny(get_response, data)
        self.assertContains(get_response, data.get("email"))
        self.assertContains(get_response, "customerprofile")  # admin only

        self.assertNotContains(get_response, self.admin_user.email)

        # testing delete / user deletion
        delete_response = self.client.delete("/accounts/users/")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(get_user_model().objects.exclude(is_admin=True))  # empty, users deleted -> False

    def test_users_list_admin_customerprofile_field(self):
        self.client.login(email=self.admin_user.email, password="passwordtest123")
        get_response = self.client.get(reverse("accounts:users_list"))

        self.assertContains(get_response, "customerprofile")

    def test_admin_users_list_get_post_delete(self):
        self.client.force_authenticate(self.admin_user)
        data = {
            "email": "new_admin@gmail.com",
            "name": "random_admin",
            "surname": "admin_surname",
            "date_of_birth": date(1995, 10, 10),
            "password": "adminadmin1",
            "password2": "adminadmin1",
        }
        url = reverse("accounts:admin_list")

        response_creation = self.client.post(url, data=data)
        self.assertEqual(response_creation.status_code, status.HTTP_201_CREATED)
        self.assertTrue(MyCustomUser.admins.get(email="new_admin@gmail.com"))

        response = self.client.get(url)
        admins = MyCustomUser.admins.all()
        all_admins = list(itertools.chain(*admins.values_list("email", "surname", "name")))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContainsAll(response, all_admins)  # all admins are listed

        delete_response = self.client.delete(url)
        admins_after_deletion = MyCustomUser.admins.all()
        self.assertEqual(len(admins_after_deletion), 1)  # "filip" not touched
        self.assertEqual(delete_response.status_code, status.HTTP_200_OK)
        self.assertContains(delete_response, "Admin Users were successfully deleted!")

    def test_token_retrieval(self):
        """
        test if user will retrieve the token upon submission of correct credentials
        """
        response = self.client.post(
            "/accounts/api-token-auth/", data={"email": "test@gmail.com", "password": "passwordtest123"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertContains(response, "token")

    def test_token_retrieval_wrong_password(self):
        """
        test if user will retrieve the token upon submission of correct credentials
        """
        response = self.client.post(
            "/accounts/api-token-auth/", data={"email": "admin@gmail.com", "password": "wrongpassword123"}
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_creation_of_tokens_after_post_save_signal(self):

        total_tokens = len(Token.objects.all())
        # should be 3 => equal to nb of users

        self.assertEqual(total_tokens, len(MyCustomUser.objects.all()))
