from rest_framework.authtoken.admin import User
from rest_framework.test import APITestCase
from main.models import Question, Section, World, Answer, StudentProfile, Class


class TestSetUp(APITestCase):
    def setUp(self):
        """
        Dummy data to test custom questions
        1x User, 1x World, 1x Section, 1x Question, 4x Answers
        """
        self.question_url = '/api/questions/'
        self.random_user1 = User.objects.create_user(username="tester1", password="tester123")
        # user = User.objects.create_user(username="tester2", password="tester123")
        self.client.force_authenticate(user=self.random_user1)

        world = World.objects.create(
            world_name="worldnametest1",
            topic="topictest1",
            is_custom_world="1",
            index="1"
        )

        section = Section.objects.create(
            sub_topic_name="subtopicnametest1",
            index="1",
            world_id=world.id
        )

        question1 = Question.objects.create(
            question="question1",
            section=section,
            difficulty="1",
            created_by_id="1"
        )

        Answer.objects.create(
            answer="answer1",
            is_correct="True",
            question_id=question1.id
        )

        Answer.objects.create(
            answer="answer2",
            is_correct="False",
            question_id=question1.id
        )

        Answer.objects.create(
            answer="answer3",
            is_correct="False",
            question_id=question1.id
        )

        Answer.objects.create(
            answer="answer4",
            is_correct="False",
            question_id=question1.id
        )

#        Question.objects.create(
#            question="question2",
#            section=section,
#            difficulty="1",
#            created_by_id="2"
#        )
