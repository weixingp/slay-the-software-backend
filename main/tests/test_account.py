from uuid import uuid4

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase

from main.models import StudentProfile, Class


class SetUp(APITestCase):
    def setUp(self):
        self.username = "test"
        self.password = "test123"
        self.user = User.objects.create_user(username="test", password="test123")
        teacher = User.objects.create_user(username="teacher", password="teacher123")
        test_class = Class.objects.create(
            teacher=teacher,
            class_name="Test Class"
        )

        StudentProfile.objects.create(student=self.user, year_of_study=2, class_group=test_class)


class TestAccount(SetUp):
    def test_first_login(self):
        """
        API: /api/account/login/
        Test login with default password (Password not yet changed)
        """

        data = {
            "username": self.username,
            "password": self.password,
        }

        res = self.client.post("/api/account/login/", data=data, format="json")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        self.assertEqual(res.data['token'], None)

    def test_login_success(self):
        """
        API: /api/account/login/
        Test login successfully
        """

        url = "/api/account/login/"
        data = {
            "username": self.username,
            "password": self.password,
        }
        self.user.student_profile.has_reset_password = True
        self.user.student_profile.save()

        res = self.client.post(url, data=data, format="json")
        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        has_token = True if res.data['token'] else False
        self.assertEqual(has_token, True)

    def test_change_password_with_same_password(self):
        """
        API: /api/account/changepassword/
        Test changing password with the same password
        """

        url = "/api/account/changepassword/"
        data = {
            "username": self.username,
            "password": self.password,
            "new_password": self.password
        }
        res = self.client.post(url, data=data, format="json")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_success(self):
        """
        API: /api/account/changepassword/
        Test changing password successfully
        """

        url = "/api/account/changepassword/"
        data = {
            "username": self.username,
            "password": self.password,
            "new_password": uuid4().hex
        }
        self.user.set_password(data['new_password'])  # This doesn't save, just using the hashed pwd fn
        hashed_pwd = self.user.password

        res = self.client.post(url, data=data, format="json")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        self.assertEqual(res.data['success'], True)
        self.assertEqual(self.user.password, hashed_pwd)

        user = User.objects.get(username=data['username'])
        self.assertEqual(user.student_profile.has_reset_password, True)
