from django.contrib.auth.models import User
from rest_framework import status

from main.tests.test_setup import TestSetUp


class TestAccount(TestSetUp):
    def test_first_login(self):
        data = {
            "username": "tester1",
            "password": "tester123",
        }

        res = self.client.post("/api/account/login/", data=data, format="json")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        self.assertEqual(res.data['token'], None)

    def test_change_password_with_same_password(self):
        """
        API: /api/account/changepassword/
        Test changing password with the same password
        """

        url = "/api/account/changepassword/"
        data = {
            "username": "tester1",
            "password": "tester123",
            "new_password": "tester123"
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
            "username": "tester1",
            "password": "tester123",
            "new_password": "tester12345"
        }
        self.random_user1.set_password(data['new_password'])  # This doesn't save, just using the hashed pwd fn
        hashed_pwd = self.random_user1.password

        res = self.client.post(url, data=data, format="json")

        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        self.assertEqual(res.data['success'], True)
        self.assertEqual(self.random_user1.password, hashed_pwd)

        user = User.objects.get(username=data['username'])
        self.assertEqual(user.student_profile.has_reset_password, True)

    def test_login_success(self):
        """
        API: /api/account/login/
        Test login successfully
        """

        url = "/api/account/login/"
        data = {
            "username": "tester1",
            "password": "tester123",
        }
        self.random_user1.student_profile.has_reset_password = True
        self.random_user1.student_profile.save()

        res = self.client.post(url, data=data, format="json")
        # Status check
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Data check
        has_token = True if res.data['token'] else False
        self.assertEqual(has_token, True)
