from rest_framework.test import APITestCase
from rest_framework import status
from main.models import User, World, Section, Level, Question, Answer, QuestionRecord
import random

class TestLeaderboardAPI(APITestCase):
    def setUp(self):
        """
        Creates a Student User and 3 Campaign Worlds
        """
        self.__create_worlds()
        self.__simulate_student1()
        self.__simulate_student2()
        self.__simulate_student3()
        self.client.force_authenticate(user=self.student1)

        self.leaderboard_url = "/api/leaderboard/"

    def __create_worlds(self):
        # create campaign worlds
        self.superuser = User.objects.create(username="tempSuperUser", password="temp", is_superuser=True,
                                             is_staff=True)

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

    def __simulate_student1(self):
        """
        Student One will have reached Level 16 and accumulated 160 points
        """
        self.student1 = User.objects.create(username="student1", password="student1_pw", first_name="Student One",
                                            last_name="Student One")

        sections = Section.objects.filter(world=self.world1)
        questions = Question.objects.filter(section__in=sections)
        points = 0
        for i in range(1,10): # first world, total points = 90
            level = Level.objects.get(id=i)
            QuestionRecord.objects.create(question=random.choice(questions), level=level, is_correct=True,
                                          points_change=10, user=self.student1)
            points += 10

        sections = Section.objects.filter(world=self.world2)
        questions = Question.objects.filter(section__in=sections)
        for i in range(10, 17):  # second world, total points = 70
            level = Level.objects.get(id=i)
            QuestionRecord.objects.create(question=random.choice(questions), level=level, is_correct=True,
                                          points_change=10, user=self.student1)

    def __simulate_student2(self):
        """
        Student Two will have reached level 25 and accumulated 250 points
        """
        self.student2 = User.objects.create(username="student2", password="student2_pw", first_name="Student Two",
                                            last_name="Student Two")

        sections = Section.objects.filter(world=self.world1)
        questions = Question.objects.filter(section__in=sections)
        for i in range(1,10):  # first world, total points = 90
            level = Level.objects.get(id=i)
            QuestionRecord.objects.create(question=random.choice(questions), level=level, is_correct=True,
                                          points_change=10, user=self.student2)

        sections = Section.objects.filter(world=self.world2)
        questions = Question.objects.filter(section__in=sections)
        for i in range(10, 19):  # second world, total points = 90
            level = Level.objects.get(id=i)
            QuestionRecord.objects.create(question=random.choice(questions), level=level, is_correct=True,
                                          points_change=10, user=self.student2)

        sections = Section.objects.filter(world=self.world3)
        questions = Question.objects.filter(section__in=sections)
        for i in range(19, 26):  # second world, total points = 70
            level = Level.objects.get(id=i)
            QuestionRecord.objects.create(question=random.choice(questions), level=level, is_correct=True,
                                          points_change=10, user=self.student2)

    def __simulate_student3(self):
        """
        Student Three will have reached level 6 and accumulated 60 points
        """
        self.student3 = User.objects.create(username="student3", password="student3_pw", first_name="Student Three",
                                            last_name="Student Three")

        sections = Section.objects.filter(world=self.world1)
        questions = Question.objects.filter(section__in=sections)
        for i in range(1,7):  # first world, total points = 60
            level = Level.objects.get(id=i)
            QuestionRecord.objects.create(question=random.choice(questions), level=level, is_correct=True,
                                          points_change=10, user=self.student3)

    def test_can_GET_leaderboard(self):
        """
        API: "api/leaderboard"
        Method: GET
        Expected result: Retrieved leaderboard with the correct:
        - rankings and ordering: Student Two (1), Student One (2), Student Three (3)
        - points per Student: Student Two (250), Student One (160), Student Three (60)
        """
        response = self.client.get(self.leaderboard_url, format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 3)
        # check rankings and order
        self.assertEqual(response_json[0]["first_name"], "Student Two")
        self.assertEqual(response_json[1]["first_name"], "Student One")
        self.assertEqual(response_json[2]["first_name"], "Student Three")
        self.assertEqual(response_json[0]["rank"], 1)
        self.assertEqual(response_json[1]["rank"], 2)
        self.assertEqual(response_json[2]["rank"], 3)
        # check points
        self.assertEqual(response_json[0]["points"], 250)
        self.assertEqual(response_json[1]["points"], 160)
        self.assertEqual(response_json[2]["points"], 60)

    def test_can_GET_with_limit(self):
        """
        API: "api/leaderboard?limit=2"
        Method: GET with query parameter limit=2
        Expected result: Retrieved leaderboard with the correct:
        - rankings and ordering: Student Two (1), Student One (2)
        - points per Student: Student Two (250), Student One (160)
        """
        response = self.client.get(self.leaderboard_url + "?limit=2", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 2)
        # check rankings and order
        self.assertEqual(response_json[0]["first_name"], "Student Two")
        self.assertEqual(response_json[1]["first_name"], "Student One")
        self.assertEqual(response_json[0]["rank"], 1)
        self.assertEqual(response_json[1]["rank"], 2)
        # check points
        self.assertEqual(response_json[0]["points"], 250)
        self.assertEqual(response_json[1]["points"], 160)

    def test_can_GET_with_offset(self):
        """
        API: "api/leaderboard?offset=2"
        Method: GET with query parameter offset=2
        Expected result: Retrieved leaderboard with the correct:
        - rankings and ordering: Student One (2), Student Three (3)
        - points per Student: Student One (170), Student Three (60)
        """
        response = self.client.get(self.leaderboard_url + "?offset=2", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 2)
        # check rankings and order
        self.assertEqual(response_json[0]["first_name"], "Student One")
        self.assertEqual(response_json[1]["first_name"], "Student Three")
        self.assertEqual(response_json[0]["rank"], 2)
        self.assertEqual(response_json[1]["rank"], 3)
        # check points
        self.assertEqual(response_json[0]["points"], 160)
        self.assertEqual(response_json[1]["points"], 60)

    def test_can_GET_with_world_1(self):
        """
        API: "api/leaderboard?world_id=1"
        Method: GET
        Expected result: Retrieved leaderboard with the correct:
        - rankings and ordering: Student One (1), Student Two (2), Student Three (3)
        - points per Student: Student One (90), Student Two (90), Student Three (60)
        """
        response = self.client.get(self.leaderboard_url + "?world_id=1", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 3)
        # check rankings and order
        self.assertEqual(response_json[0]["first_name"], "Student One")
        self.assertEqual(response_json[1]["first_name"], "Student Two")
        self.assertEqual(response_json[2]["first_name"], "Student Three")
        self.assertEqual(response_json[0]["rank"], 1)
        self.assertEqual(response_json[1]["rank"], 2)
        self.assertEqual(response_json[2]["rank"], 3)
        # check points
        self.assertEqual(response_json[0]["points"], 90)
        self.assertEqual(response_json[1]["points"], 90)
        self.assertEqual(response_json[2]["points"], 60)

    def test_can_GET_with_world_2(self):
        """
        API: "api/leaderboard?world_id=2"
        Method: GET
        Expected result: Retrieved leaderboard with the correct:
        - rankings and ordering: Student Two (1), Student One (2)
        - points per Student: Student Two (90), Student One (80)
        """
        response = self.client.get(self.leaderboard_url + "?world_id=2", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response_json), 2)
        # check rankings and order
        self.assertEqual(response_json[0]["first_name"], "Student Two")
        self.assertEqual(response_json[1]["first_name"], "Student One")
        self.assertEqual(response_json[0]["rank"], 1)
        self.assertEqual(response_json[1]["rank"], 2)
        # check points
        self.assertEqual(response_json[0]["points"], 90)
        self.assertEqual(response_json[1]["points"], 70)

    def test_can_GET_with_user(self):
        """
        API: "api/leaderboard?user_id=4"
        Method: GET
        Expected result: Retrieved leaderboard with the correct:
        - rankings and ordering: Student Three (3)
        - points per Student: Student Three (60)
        """
        response = self.client.get(self.leaderboard_url + "?user_id=4", format="json")
        response_json = response.json()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # check rankings and order
        self.assertEqual(response_json["first_name"], "Student Three")
        self.assertEqual(response_json["rank"], 3)
        # check points
        self.assertEqual(response_json["points"], 60)