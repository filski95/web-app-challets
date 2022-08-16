from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APITestCase

from .models import MyCustomUser
from .serializers import MyCustomUserSerializer


class MyCustomUserTest(TestCase):
    def assertContainsAny(self, response, texts, status_code=200, msg_prefix="", html=False):
        """assert contains for multiple values"""
        total_count = 0
        for text in texts:
            text_repr, real_count, msg_prefix = self._assert_contains(response, text, status_code, msg_prefix, html)
            total_count += real_count

        self.assertTrue(total_count != 0)

    def test_user_creation(self):

        testuser = MyCustomUser.objects.create_user(email="test@gmail.com", name="testname", surname="testsurname")

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
            email="test@gmail.com", name="testname", surname="testsurname"
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
                email="super@user.com", name="testname", surname="testsurname", password="foo", is_superuser=False
            )


class MyCustomUserTestAPI(TestCase):
    @classmethod
    def setUpTestData(cls) -> None:
        cls.serializer = MyCustomUserSerializer
