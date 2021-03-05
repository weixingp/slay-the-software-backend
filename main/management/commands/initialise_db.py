from django.core.management.base import BaseCommand, CommandError
from main.models import *
from django.utils import timezone
import random

class Command(BaseCommand):
    help = 'Initialises the database. Make sure to run "python manage.py flush" first.'

    def __init__(self):
        super().__init__()
        self.completed_time = timezone.now() + timezone.timedelta(days=2)

    def handle(self, *args, **options):
        self.__create_superusers()
        self.__create_teachers()
        self.__create_students()
        self.__create_campaign_mode()
        self.__simulate_student1_progress()
        self.__simulate_student2_progress()
        self.__simulate_student3_progress()

    def __create_superusers(self):
        self.stdout.write("Creating superusers...")
        User.objects.create_superuser(username="admin", password="admin123")
        User.objects.create_superuser(username="weixing", password="weixing123")
        User.objects.create_superuser(username="favian", password="favian123")
        User.objects.create_superuser(username="junwei", password="junwei123")
        self.stdout.write("...complete")

    def __create_teachers(self):
        self.stdout.write("Creating teachers...")
        User.objects.create_user(username="nicole", password="nicole123", first_name="Nicole", last_name="Tan",
                                 is_staff=True)
        User.objects.create_user(username="zhenying", password="zhenyin123", first_name="Zhen Ying", last_name="Ngiam",
                                 is_staff=True)
        self.stdout.write("...complete")

    def __create_students(self):
        self.stdout.write("Creating students...")
        User.objects.create_user(username="wanqian", password="wanqian123", first_name="Qian", last_name="Wan")
        User.objects.create_user(username="josh", password="josh123", first_name="Josh", last_name="Lim")
        User.objects.create_user(username="shenrui", password="shenrui123", first_name="Shen Rui", last_name="Chong")
        self.stdout.write("...complete")

    def __create_campaign_mode(self):
        """
        Creates 3 Worlds for Campaign Mode.
        Each World has 3 Sections, and each Section has 4 Levels.
        """
        self.stdout.write("Creating data for Campaign Mode...")
        aquila = World.objects.create(world_name="Aquila", topic="Requirements Analysis", index=1)
        bootes = World.objects.create(world_name="Bootes", topic="Software Architecture Styles", index=2)
        cassiopeia = World.objects.create(world_name="Cassiopeia", topic="Software Testing", index=3)

        # create sections for aquila
        self.__create_section(aquila, "Requirements Elicitation", 1, False)
        self.__create_section(aquila, "Conceptual Models", 2, False)
        self.__create_section(aquila, "Dynamic Models", 3, True)

        # create sections for bootes
        self.__create_section(bootes, "Individual Components Style", 4, False)
        self.__create_section(bootes, "Pipe-and-Filter Style", 5, False)
        self.__create_section(bootes, "Layered Style", 6, True)

        # create sections for cassiopeia
        self.__create_section(cassiopeia, "White Box Testing", 7, False)
        self.__create_section(cassiopeia, "Black Box Testing", 8, False)
        self.__create_section(cassiopeia, "User Acceptance Testing", 9, True)
        self.stdout.write("...complete")

    def __create_section(self, world, sub_topic_name, index, has_final_boss):
        section = Section.objects.create(world=world, sub_topic_name=sub_topic_name, index=index)

        # create levels
        Level.objects.create(section=section, level_name="Level One", index=index * 4 - 3)
        Level.objects.create(section=section, level_name="Level Two", index=index * 4 - 2)
        Level.objects.create(section=section, level_name="Level Three", index=index * 4 - 1)

        if has_final_boss:
            Level.objects.create(section=section, level_name="Final Boss Level", index=index * 4,
                                 is_final_boss_level=True)
        else:
            Level.objects.create(section=section, level_name="Boss Level", index=index * 4, is_boss_level=True)

        # create questions for this section
        self.__create_questions_and_answers(section, has_final_boss)

    def __create_questions_and_answers(self, section, has_final_boss):
        """
        Creates 21 Questions for Sections without Final Boss, 27 Questions for Sections with Final Boss.
        There is an even distribution of difficulty levels.
        """
        sp_user1 = User.objects.get(username="weixing")
        sp_user2 = User.objects.get(username="favian")
        sp_user3 = User.objects.get(username="junwei")

        if has_final_boss:
            upper_limit = 10
        else:
            upper_limit = 8

        for i in range(1, upper_limit):
            q1 = Question.objects.create(section=section, question="Question %s" % (i * 3 - 2), difficulty="1",
                                         created_by=sp_user1)
            q2 = Question.objects.create(section=section, question="Question %s" % (i * 3 - 1), difficulty="2",
                                         created_by=sp_user2)
            q3 = Question.objects.create(section=section, question="Question %s" % (i * 3), difficulty="3",
                                         created_by=sp_user3)

            # create answers for each question
            self.__create_answers_for_questions(q1)
            self.__create_answers_for_questions(q2)
            self.__create_answers_for_questions(q3)

    def __create_answers_for_questions(self, question):
        Answer.objects.create(question=question, answer="Answer 1")
        Answer.objects.create(question=question, answer="Answer 2")
        Answer.objects.create(question=question, answer="Answer 3")
        Answer.objects.create(question=question, answer="Answer 4", is_correct=True)

    def __simulate_student1_progress(self):
        self.stdout.write("Simulating Student 1...")
        # Student1 will have finished 1 World, and 2 Sections in another World
        student = User.objects.get(username="wanqian")

        # add records for finished world
        completed_world = World.objects.get(id=1)
        UserWorldProgressRecord.objects.create(user=student, world=completed_world, is_completed=True,
                                               completed_time=self.completed_time)
        # add level and question records for finished world
        sections = Section.objects.filter(world=completed_world)
        for section in sections:
            levels = Level.objects.filter(section=section)
            questions = Question.objects.filter(section=section)
            for level in levels:
                UserLevelProgressRecord.objects.create(user=student, level=level, is_completed=True,
                                                       completed_time=self.completed_time)
                if level.is_final_boss_level:
                    num_of_questions_to_add = 10
                else:
                    num_of_questions_to_add = 3
                for i in range(num_of_questions_to_add):
                    question = random.choice(questions)
                    QuestionRecord.objects.create(user=student, question=question, level=level, is_correct=True,
                                                  points_change=int(question.difficulty), reason="Correct",
                                                  is_completed=True, completed_time=self.completed_time)
        # add records for partially finished world
        partially_completed_world = World.objects.get(id=2)
        UserWorldProgressRecord.objects.create(user=student, world=partially_completed_world)
        # add level and question records for partially finished world
        sections = Section.objects.filter(world=partially_completed_world)[:2] # change num of completed sections here
        for section in sections:
            levels = Level.objects.filter(section=section)
            questions = Question.objects.filter(section=section)
            for level in levels:
                UserLevelProgressRecord.objects.create(user=student, level=level, is_completed=True,
                                                       completed_time=self.completed_time)
                if level.is_final_boss_level:
                    num_of_questions_to_add = 10
                else:
                    num_of_questions_to_add = 3
                for i in range(num_of_questions_to_add):
                    question = random.choice(questions)
                    QuestionRecord.objects.create(user=student, question=question, level=level, is_correct=True,
                                                  points_change=int(question.difficulty), reason="Correct",
                                                  is_completed=True, completed_time=self.completed_time)
        self.stdout.write("...complete")

    def __simulate_student2_progress(self):
        self.stdout.write("Simulating Student 2...")
        # Student2 will have finished 2 Worlds, and has cleared 3 Levels in the 1st Section of the last World
        student = User.objects.get(username="josh")

        # add records for finished world
        completed_worlds = World.objects.filter(id__range=(0, 2)) # change here for num of finished worlds
        for world in completed_worlds:
            UserWorldProgressRecord.objects.create(user=student, world=world, is_completed=True,
                                                   completed_time=self.completed_time)
            # add level and question records for finished world
            sections = Section.objects.filter(world=world)
            for section in sections:
                levels = Level.objects.filter(section=section)
                questions = Question.objects.filter(section=section)
                for level in levels:
                    UserLevelProgressRecord.objects.create(user=student, level=level, is_completed=True,
                                                           completed_time=self.completed_time)
                    if level.is_final_boss_level:
                        num_of_questions_to_add = 10
                    else:
                        num_of_questions_to_add = 3
                    for i in range(num_of_questions_to_add):
                        question = random.choice(questions)
                        QuestionRecord.objects.create(user=student, question=question, level=level, is_correct=True,
                                                      points_change=int(question.difficulty), reason="Correct",
                                                      is_completed=True, completed_time=self.completed_time)

        # add records for partially finished world
        partially_completed_world = World.objects.get(id=3)
        UserWorldProgressRecord.objects.create(user=student, world=partially_completed_world)
        # add level and question records for partially finished world
        section = Section.objects.filter(world=partially_completed_world)[0]
        levels = Level.objects.filter(section=section)[:3]
        questions = Question.objects.filter(section=section)
        for level in levels:
            UserLevelProgressRecord.objects.create(user=student, level=level, is_completed=True,
                                                   completed_time=self.completed_time)
            num_of_questions_to_add = 3
            for i in range(num_of_questions_to_add):
                question = random.choice(questions)
                QuestionRecord.objects.create(user=student, question=question, level=level, is_correct=True,
                                              points_change=int(question.difficulty), reason="Correct",
                                              is_completed=True, completed_time=self.completed_time)
        self.stdout.write("...complete")

    def __simulate_student3_progress(self):
        self.stdout.write("Simulating Student 3...")
        # Student3 will have finished 11 Levels (so 2/3 Sections completed) of the 1st World,
        # with the Final Boss Level not cleared yet
        student = User.objects.get(username="shenrui")
        # add records for partially finished world
        partially_completed_world = World.objects.get(id=1)
        UserWorldProgressRecord.objects.create(user=student, world=partially_completed_world)
        # add level and question records for completed sections
        sections = Section.objects.filter(world=partially_completed_world)[:2]
        for section in sections:
            levels = Level.objects.filter(section=section)
            questions = Question.objects.filter(section=section)
            for level in levels:
                UserLevelProgressRecord.objects.create(user=student, level=level, is_completed=True,
                                                       completed_time=self.completed_time)
                if level.is_final_boss_level:
                    num_of_questions_to_add = 10
                else:
                    num_of_questions_to_add = 3
                for i in range(num_of_questions_to_add):
                    question = random.choice(questions)
                    QuestionRecord.objects.create(user=student, question=question, level=level, is_correct=True,
                                                  points_change=int(question.difficulty), reason="Correct",
                                                  is_completed=True, completed_time=self.completed_time)
        # add level and question records for last incomplete section
        section = Section.objects.filter(world=partially_completed_world)[2]
        levels = Level.objects.filter(section=section)[:3]
        questions = Question.objects.filter(section=section)
        for level in levels:
            UserLevelProgressRecord.objects.create(user=student, level=level, is_completed=True,
                                                   completed_time=self.completed_time)
            num_of_questions_to_add = 3
            for i in range(num_of_questions_to_add):
                question = random.choice(questions)
                QuestionRecord.objects.create(user=student, question=question, level=level, is_correct=True,
                                              points_change=int(question.difficulty), reason="Correct",
                                              is_completed=True, completed_time=self.completed_time)
        self.stdout.write("...complete")