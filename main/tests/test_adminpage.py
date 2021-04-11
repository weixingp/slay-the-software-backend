from django.test import TestCase, Client
from rest_framework.authtoken.admin import User
from main.models import *


class TestAdminPage(TestCase):
    def create_superuser(self):
        """
        Creates a Superuser
        """
        self.username = "test"
        self.password = "test"
        user = User.objects.create_user(username=self.username,email="test@email.com", password=self.password)
        user.is_staff = True
        user.is_superuser = True
        user.is_active = True
        user.save()
        self.user = user

    def test_superuser(self):
        """
        Creates one world for campaign_statistics testing

        Test if Superuser has access to all of the admin pages
        """
        self.test_world = World.objects.create(world_name="test_world", topic="Requirements Analysis", index=1)
        self.create_superuser()
        client = Client()
        client.login(username=self.username, password=self.password)
        admin_pages = [
            "/admin/",
            "/admin/auth/",
            "/admin/authtoken/token/",
            "/admin/auth/group/",
            "/admin/auth/user/",
            "/admin/main/assignment/",
            "/admin/main/customworld/",
            "/admin/main/level/",
            "/admin/main/question/",
            "/admin/main/section/",
            "/admin/main/studentprofile/",
            "/admin/main/world/",
            "/admin/campaign_statistics/",
            "/admin/assignment_statistics/",
            "/admin/import-users/",
        ]
        for page in admin_pages:
            response = client.get(page)
            assert response.status_code == 200
