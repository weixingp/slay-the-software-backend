from django.contrib.auth.models import User
from rest_framework.test import APITestCase

from main.models import Class, StudentProfile, World, Level, Section, Question, Answer


class FullSetUp(APITestCase):
    def setUp(self):
        self.__create_classes()
        self.__create_accounts()
        self.client.force_authenticate(user=self.user)
        self.__create_campaign_mode()

    def __create_accounts(self):
        self.username = "test"
        self.password = "test123"

        # Player creation

        self.user = User.objects.create_user(username=self.username, password=self.password)
        StudentProfile.objects.create(student=self.user, year_of_study=2, class_group=self.test_class)

    def __create_classes(self):
        self.teacher = User.objects.create_user(username="teacher", password="teacher123")
        self.test_class = Class.objects.create(
            teacher=self.teacher,
            class_name="Test Class"
        )
    def __create_campaign_mode(self):
        """
        Creates 3 Worlds for Campaign Mode.
        Each World has 3 Sections, and each Section has 3 Levels.
        Last Level of the first 2 Section is a Mini Boss Level.
        Last Level of the 3rd and last Section is the Final Boss Level.
        """
        world1 = World.objects.create(world_name="Dusza", topic="Requirements Analysis", index=1)
        world2 = World.objects.create(world_name="Wonders", topic="Software Architecture Styles", index=2)
        world3 = World.objects.create(world_name="Zeha", topic="Software Testing", index=3)

        # create sections for world 1
        self.__create_section(world1, "Requirements Elicitation", 1, False)
        self.__create_section(world1, "Conceptual Models", 2, False)
        self.__create_section(world1, "Dynamic Models", 3, True)

        # create sections for world 2
        self.__create_section(world2, "Individual Components Style", 4, False)
        self.__create_section(world2, "Pipe-and-Filter Style", 5, False)
        self.__create_section(world2, "Layered Style", 6, True)

        # create sections for world 3
        self.__create_section(world3, "White Box Testing", 7, False)
        self.__create_section(world3, "Black Box Testing", 8, False)
        self.__create_section(world3, "User Acceptance Testing", 9, True)

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
        Creates 21 Questions for Sections without Final Boss, 27 Questions for Sections with Final Boss.
        There is an even distribution of difficulty levels.
        """

        if has_final_boss:
            upper_limit = 10
        else:
            upper_limit = 8

        for i in range(1, upper_limit):
            q1 = Question.objects.create(section=section, question="Question %s" % (i * 3 - 2), difficulty="1",
                                         created_by=self.user)
            q2 = Question.objects.create(section=section, question="Question %s" % (i * 3 - 1), difficulty="2",
                                         created_by=self.user)
            q3 = Question.objects.create(section=section, question="Question %s" % (i * 3), difficulty="3",
                                         created_by=self.user)

            # create answers for each question
            self.__create_answers_for_questions(q1)
            self.__create_answers_for_questions(q2)
            self.__create_answers_for_questions(q3)

    def __create_answers_for_questions(self, question):
        Answer.objects.create(question=question, answer="Answer 1")
        Answer.objects.create(question=question, answer="Answer 2")
        Answer.objects.create(question=question, answer="Answer 3")
        Answer.objects.create(question=question, answer="Answer 4", is_correct=True)
