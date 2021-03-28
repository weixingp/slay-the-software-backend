from rest_framework.test import APITestCase
from rest_framework import status
from main.models import User, World, Section, Level, Question, Answer

class TestWorldsAPI(APITestCase):
    def setUp(self):
        """
        Creates a Student User and 3 Campaign Worlds
        """
        self.student = User.objects.create(username="testUser", password="testUserPw")
        self.client.force_authenticate(user=self.student)

        # create campaign worlds
        self.superuser = User.objects.create(username="tempSuperUser", password="temp", is_superuser=True, is_staff=True)

        self.world1 = World.objects.create(world_name="Dusza", topic="Requirements Analysis", index=1)
        self.world2 = World.objects.create(world_name="Wonders", topic="Software Architecture Styles", index=2)
        self.world3 = World.objects.create(world_name="Zeha", topic="Software Testing", index=3)

        # create sections for world 1
        self.__create_section(self.world1, "Requirements Elicitation", 1, False)
        self.__create_section(self.world1, "Conceptual Models", 2, False)
        self.__create_section(self.world1, "Dynamic Models", 3, True)

        # create sections for world 2
        self.__create_section(self.world2, "Design Patterns (1)", 4, False)
        self.__create_section(self.world2, "Design Patterns (2)", 5, False)
        self.__create_section(self.world2, "MVC", 6, True)

        # create sections for world 3
        self.__create_section(self.world3, "White Box Testing", 7, False)
        self.__create_section(self.world3, "Black Box Testing", 8, False)
        self.__create_section(self.world3, "User Acceptance Testing", 9, True)

        self.worlds_url = "/api/worlds/"

    def __create_section(self, world, sub_topic_name, index, has_final_boss):
        section = Section.objects.create(world=world, sub_topic_name=sub_topic_name, index=index)

        # create levels
        Level.objects.create(section=section, level_name="Level One", index=index * 3 - 2)
        Level.objects.create(section=section, level_name="Level Two", index=index * 3 - 1)

        if has_final_boss:
            Level.objects.create(section=section, level_name="Final Boss Level", index=index * 3,
                                 is_final_boss_level=True)
        else:
            Level.objects.create(section=section, level_name="Boss Level", index=index * 3, is_boss_level=True)

        # create questions for this section
        self.__create_questions_and_answers(section, has_final_boss)

    def __create_questions_and_answers(self, section, has_final_boss):
        """
        Creates 9 Questions for Sections without Final Boss, 16 Questions for Sections with Final Boss.
        There is an even distribution of difficulty levels.
        """
        if has_final_boss:
            upper_limit = 5
        else:
            upper_limit = 4

        for i in range(1, upper_limit):
            q1 = Question.objects.create(section=section, question="Question %s" % (i * 3 - 2), difficulty="1",
                                         created_by=self.superuser)
            q2 = Question.objects.create(section=section, question="Question %s" % (i * 3 - 1), difficulty="2",
                                         created_by=self.superuser)
            q3 = Question.objects.create(section=section, question="Question %s" % (i * 3), difficulty="3",
                                         created_by=self.superuser)

            # create answers for each question
            self.__create_answers_for_questions(q1)
            self.__create_answers_for_questions(q2)
            self.__create_answers_for_questions(q3)

    def __create_answers_for_questions(self, question):
        Answer.objects.create(question=question, answer="Answer 1")
        Answer.objects.create(question=question, answer="Answer 2")
        Answer.objects.create(question=question, answer="Answer 3")
        Answer.objects.create(question=question, answer="Answer 4", is_correct=True)

    def test_can_GET_worlds(self):
        """
        API: "api/worlds/"
        Method: GET
        Expected result: Get 3 Worlds, all with is_custom_world = False
        """
        response = self.client.get(self.worlds_url, format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 3)
        self.assertEqual(response_json[0]["is_custom_world"], False)
        self.assertEqual(response_json[1]["is_custom_world"], False)
        self.assertEqual(response_json[2]["is_custom_world"], False)

    def test_can_GET_specific_worlds(self):
        """
        API: "api/worlds/:id/
        Method: GET
        Expected result: Each of the 3 Worlds can be retrieved individually, all with is_custom_world = False
        """
        response = self.client.get(self.worlds_url + str(self.world1.id) + "/", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["is_custom_world"], False)

        response = self.client.get(self.worlds_url + str(self.world2.id) + "/", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["is_custom_world"], False)

        response = self.client.get(self.worlds_url + str(self.world3.id) + "/", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response_json["is_custom_world"], False)