from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from main.models import *
from django.utils import timezone
import random
from main import GameManager as gm

points_map = {
    "1": 5,
    "2": 10,
    "3": 15
}

class Command(BaseCommand):
    help = 'Initialises the database. Make sure to run "python manage.py flush" first.'

    def __init__(self):
        super().__init__()
        self.completed_time = timezone.now() + timezone.timedelta(days=2)
        self.assignment_deadline = timezone.now() + timezone.timedelta(days=7)

    def handle(self, *args, **options):
        self.__create_superusers()
        self.__create_teachers()
        self.__create_students()
        self.__create_campaign_mode()
        self.__simulate_student1_progress()
        self.__simulate_student2_progress()
        self.__simulate_student3_progress()
        self.__create_custom_worlds()
        self.__create_assignments()
        #self.__simulate_assignment_playthroughs()


    def __create_superusers(self):
        self.stdout.write("Creating superusers...")
        User.objects.create_superuser(username="admin", password="admin123")
        User.objects.create_superuser(username="weixing", password="weixing123")
        User.objects.create_superuser(username="favian", password="favian123")
        User.objects.create_superuser(username="junwei", password="junwei123")
        self.stdout.write("...superusers created")

    def __create_teachers(self):
        self.stdout.write("Creating teachers...")

        # create teacher group and set permissions
        teacher_group = Group.objects.create(name="Teachers")
        permission_verbs = ["add", "change", "delete", "view"]
        required_models = ["user", "question", "customworld", "assignment"]
        for model in required_models:
            for verb in permission_verbs:
                teacher_group.permissions.add(
                    Permission.objects.get(codename=verb+"_"+model)
                )

        teachers = [{"username": "nicole", "password": "nicole123", "first_name": "Nicole", "last_name": "Tan", "class": "SSP1"},
                    {"username": "zhenying", "password": "zhenyin123", "first_name": "Zhen Ying", "last_name": "Ngiam", "class": "SSP2"}]
        for teacher in teachers:
            created_teacher = User.objects.create_user(username=teacher["username"], password=teacher["password"],
                                                       first_name=teacher["first_name"], last_name=teacher["last_name"],
                                                       is_staff=True)
            teacher_group.user_set.add(created_teacher)
            Class.objects.create(teacher=created_teacher, class_name=teacher["class"])

        self.stdout.write("...teachers created")

    def __create_students(self):
        self.stdout.write("Creating students...")
        students = [{"username": "wanqian", "password": "wanqian123", "first_name": "Wan", "last_name": "Qian", "class": "SSP1"},
                    {"username": "josh", "password": "josh123", "first_name": "Josh", "last_name": "Lim", "class": "SSP1"},
                    {"username": "shenrui", "password": "shenrui123", "first_name": "Shen Rui", "last_name": "Chong", "class": "SSP1"},
                    {"username": "tom", "password": "tom123", "first_name": "Tom", "last_name": "Tan", "class": "SSP2"},
                    {"username": "mary", "password": "mary123", "first_name": "Mary", "last_name": "Lee", "class": "SSP2"},
                    {"username": "jerry", "password": "jerry123", "first_name": "Jerry", "last_name": "Chua", "class": "SSP2"},
                    {"username": "ayden", "password": "ayden123", "first_name": "Ayden", "last_name": "Wong", "class": "SSP2"},
                    {"username": "jayden", "password": "jayden123", "first_name": "Jayden", "last_name": "Seah", "class": "SSP2"},]
        for student in students:
            created_student = User.objects.create_user(username=student["username"], password=student["password"],
                                                       first_name=student["first_name"], last_name=student["last_name"])
            class_group = Class.objects.get(class_name=student["class"])
            StudentProfile.objects.create(student=created_student, year_of_study=2, class_group=class_group)
        self.stdout.write("...students created")

    def __create_campaign_mode(self):
        """
        Creates 3 Worlds for Campaign Mode.
        Each World has 3 Sections, and each Section has 3 Levels.
        Last Level of the first 2 Section is a Mini Boss Level.
        Last Level of the 3rd and last Section is the Final Boss Level.
        """
        self.stdout.write("Creating data for Campaign Mode...")
        aquila = World.objects.create(world_name="Dusza", topic="Requirements Analysis", index=1)
        bootes = World.objects.create(world_name="Wonders", topic="Software Architecture Styles", index=2)
        cassiopeia = World.objects.create(world_name="Zeha", topic="Software Testing", index=3)

        # create sections for world 1
        self.__create_section(aquila, "Requirements Elicitation", 1, False)
        self.__create_section(aquila, "Conceptual Models", 2, False)
        self.__create_section(aquila, "Dynamic Models", 3, True)

        # create sections for world 2
        self.__create_section(bootes, "Individual Components Style", 4, False)
        self.__create_section(bootes, "Pipe-and-Filter Style", 5, False)
        self.__create_section(bootes, "Layered Style", 6, True)

        # create sections for world 3
        self.__create_section(cassiopeia, "White Box Testing", 7, False)
        self.__create_section(cassiopeia, "Black Box Testing", 8, False)
        self.__create_section(cassiopeia, "User Acceptance Testing", 9, True)
        self.stdout.write("...all data for Campaign Mode created")

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
                                                  points_change=points_map[question.difficulty], reason="Correct",
                                                  is_completed=True, completed_time=self.completed_time)
        # add records for partially finished world
        partially_completed_world = World.objects.get(id=2)
        UserWorldProgressRecord.objects.create(user=student, world=partially_completed_world)
        # add level and question records for partially finished world
        sections = Section.objects.filter(world=partially_completed_world)[:2]  # change num of completed sections here
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
                                                  points_change=points_map[question.difficulty], reason="Correct",
                                                  is_completed=True, completed_time=self.completed_time)

        # unlock next level (PLEASE UPDATE THIS IF ANY CHANGES ARE MADE TO SIMULATION CAUSE I HARDCODED THIS)
        next_level = Level.objects.get(id=16)
        UserLevelProgressRecord.objects.create(user=student, level=next_level)

        self.stdout.write("...finished simulating Student 1")

    def __simulate_student2_progress(self):
        self.stdout.write("Simulating Student 2...")
        # Student2 will have finished 2 Worlds, and has cleared 3 Levels in the 1st Section of the last World
        student = User.objects.get(username="josh")

        # add records for finished world
        completed_worlds = World.objects.filter(id__range=(0, 2))  # change here for num of finished worlds
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
                                                      points_change=points_map[question.difficulty], reason="Correct",
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
                                              points_change=points_map[question.difficulty], reason="Correct",
                                              is_completed=True, completed_time=self.completed_time)

        # unlock next level (PLEASE UPDATE THIS IF ANY CHANGES ARE MADE TO SIMULATION CAUSE I HARDCODED THIS)
        next_level = Level.objects.get(id=22)
        UserLevelProgressRecord.objects.create(user=student, level=next_level)

        self.stdout.write("...finished simulating Student 2")

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
                                                  points_change=points_map[question.difficulty], reason="Correct",
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
                                              points_change=points_map[question.difficulty], reason="Correct",
                                              is_completed=True, completed_time=self.completed_time)

        # unlock next level (PLEASE UPDATE THIS IF ANY CHANGES ARE MADE TO SIMULATION CAUSE I HARDCODED THIS)
        next_level = Level.objects.get(id=10)
        UserLevelProgressRecord.objects.create(user=student, level=next_level)

        self.stdout.write("...finished simulating Student 3")

    def __create_custom_worlds(self):
        '''
        Creates a Custom World for each of the 3 Students
        '''
        self.stdout.write("Creating Custom Worlds...")

        students = User.objects.filter(is_superuser=False, is_staff=False)[:3]
        topics = ["Class Diagrams", "Sequence Diagrams", "Use Case Model"]
        for i in range(len(students)):
            # create world and section
            student = students[i]
            world_name = student.first_name + "'s World"
            access_code = student.first_name[:3].upper() + "000"
            custom_world = CustomWorld.objects.create(world_name=world_name, topic=topics[i], is_custom_world=True, access_code=access_code, created_by=student)
            section = Section.objects.create(world=custom_world, sub_topic_name=topics[i])

            # create 3 levels
            for i in range(3):
                # create Level
                level_name = "Custom Level " + str(i + 1)
                Level.objects.create(section=section, level_name=level_name)

            # create 12 Questions
            for j in range(12):
                question_text = "Custom Question " + str(j + 1)
                question = Question.objects.create(question=question_text, section=section, difficulty="1",
                                                   created_by=student)
                # create Answers
                Answer.objects.create(question=question, answer="Custom Answer 1")
                Answer.objects.create(question=question, answer="Custom Answer 2")
                Answer.objects.create(question=question, answer="Custom Answer 3")
                Answer.objects.create(question=question, answer="Custom Answer 4", is_correct=True)

        self.stdout.write("...Custom Worlds created")

    def __create_assignments(self):
        '''
        Creates an Assignment for each of the 2 Teachers
        '''
        self.stdout.write("Creating assignments...")

        teachers = User.objects.filter(is_staff=True, is_superuser=False)
        topics = ["Strategy Pattern", "Observer Pattern"]
        for i in range(len(teachers)):
            teacher = teachers[i]

            # create custom world first
            world_name = topics[i]
            access_code = teacher.first_name[:3].upper() + "000"
            custom_world = CustomWorld.objects.create(world_name=world_name, topic=topics[i], is_custom_world=True,
                                                      access_code=access_code, created_by=teacher)
            section = Section.objects.create(world=custom_world, sub_topic_name=topics[i])

            # create 3 levels
            for j in range(3):
                # create Level
                level_name = "Assignment Level " + str(j + 1)
                Level.objects.create(section=section, level_name=level_name)

            # create 12 questions
            for k in range(12):
                question_text = "Assignment Question " + str(k+1)
                question = Question.objects.create(question=question_text, section=section, difficulty="1",
                                                   created_by=teacher)
                # create Answers
                Answer.objects.create(question=question, answer="Assignment Answer 1")
                Answer.objects.create(question=question, answer="Assignment Answer 2")
                Answer.objects.create(question=question, answer="Assignment Answer 3")
                Answer.objects.create(question=question, answer="Assignment Answer 4", is_correct=True)

            # create assignment
            class_group = Class.objects.get(teacher=teacher)
            Assignment.objects.create(custom_world=custom_world, class_group=class_group, name=topics[i], deadline=self.assignment_deadline)

        self.stdout.write("...assignments created")

    # def __simulate_assignment_playthroughs(self):
    #     """
    #     First Assignment will be played 2 times
    #     Second Assignment will be played 1 time
    #     """
    #
    #     # Assignment 1
    #     assignment1 = Assignment.objects.get(id=1).custom_world
    #     assignment1_section = Section.objects.get(world=assignment1)
    #     questions = Question.objects.filter(section=assignment1_section)
    #     students = User.objects.filter(id__range=(8,10))
    #     for student in students:
