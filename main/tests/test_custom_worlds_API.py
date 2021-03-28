from rest_framework.test import APITestCase
from rest_framework import status
from main.models import User, CustomWorld


class TestCustomWorldsAPI(APITestCase):
    def setUp(self):
        """
        Creates a Student User and 2 Custom Worlds created by the same Student
        """
        self.student = User.objects.create(username="testUser", password="testUserPw")
        self.client.force_authenticate(user=self.student)
        self.custom_world = CustomWorld.objects.create(world_name="Custom World Set Up 1", topic="Testing 1",
                                                       is_custom_world=True, access_code="TEST00",
                                                       created_by=self.student)
        self.custom_world = CustomWorld.objects.create(world_name="Custom World Set Up 2", topic="Testing 2",
                                                       is_custom_world=True, access_code="TEST01",
                                                       created_by=self.student)
        self.custom_world_url = "/api/worlds/custom/"

    def test_can_POST_custom_world(self):
        """
        API: "/api/worlds/custom/"
        Method: POST
        Expected result: Should be able to POST successfully
        """
        world_name = "Test POST Custom World"
        topic = "Testing POST"
        data = {
            "world_name": world_name,
            "topic": topic,
        }
        response = self.client.post(self.custom_world_url, data, format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response_json["world_name"], world_name)
        self.assertEqual(response_json["topic"], topic)
        self.assertEqual(len(response_json["sections"]), 1)  # should have 1 section
        self.assertEqual(len(response_json["sections"][0]["levels"]), 4) # should have 4 levels
        self.assertEqual(response_json["created_by"], self.student.id)

    def test_can_GET_custom_worlds(self):
        """
        API: "api/worlds/custom/"
        Method: POST
        Expected result: Should receive two custom worlds
        """
        response = self.client.get(self.custom_world_url, format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 2)

    def test_can_GET_specific_custom_world(self):
        """
        API: "api/worlds/custom/:access_code/
        Method: GET
        Expected result: Correct Custom World returned
        """
        access_code = "TEST00"
        response = self.client.get(self.custom_world_url + access_code + "/", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["access_code"], access_code)
        self.assertEqual(response_json["world_name"], "Custom World Set Up 1")

    def test_can_PUT_custom_world(self):
        """
        API: "api/worlds/custom/:access_code/
        Method: PUT
        Expected result: Custom World's name and topic changed
        """
        new_world_name = "Updated Name"
        new_topic = "Test PUT"
        access_code = "TEST00"
        data = {
            "world_name": new_world_name,
            "topic": new_topic
        }

        response = self.client.put(self.custom_world_url + access_code + "/", data, format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["world_name"], new_world_name)
        self.assertEqual(response_json["topic"], new_topic)
        self.assertEqual(response_json["access_code"], access_code)

    def test_can_DELETE_custom_world(self):
        """
        API: "api/worlds/custom/:access_code/
        Method: PUT
        Expected result: Custom World successfully deleted
        """
        access_code = "TEST00"
        response = self.client.delete(self.custom_world_url + access_code + "/", format="json")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)