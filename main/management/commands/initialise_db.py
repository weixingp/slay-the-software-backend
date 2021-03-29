from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from rest_framework.exceptions import PermissionDenied

from main.models import *
from django.utils import timezone
import random
from main.GameManager import GameManager

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
        self.answers_boolean = [True, False]
        self.correct_answer_prob = [0.7, 0.3]

    def handle(self, *args, **options):
        self.__create_superusers()
        self.__create_teachers()
        self.__create_students()
        self.__create_campaign_mode()
        self.__simulate_students_campaign_mode()
        self.__create_challenge_mode()
        self.__create_assignments()
        self.__simulate_challenge_mode_playthroughs()
        self.__simulate_assignment_playthroughs()
        self.__create_demo_challenge_mode()
        self.__create_demo_assignment()
        self.__simulate_demo_steve()

    def __create_superusers(self):
        self.stdout.write("Creating superusers...")
        User.objects.create_superuser(username="admin", password="admin123")
        User.objects.create_superuser(username="weixing", password="weixing123")
        User.objects.create_superuser(username="favian", password="favian123")
        User.objects.create_superuser(username="junwei", password="junwei123")
        self.stdout.write("...superusers created")

    def __create_teachers(self):
        '''
        Creates the following 4 Teachers:
        - Nicole: SSP1, SSP2
        - Zhen Ying: SSP3, SSP4
        '''

        self.stdout.write("Creating teachers...")

        # create teacher group and set permissions
        teacher_group = Group.objects.create(name="Teachers")
        permission_verbs = ["add", "change", "delete", "view"]
        required_models = ["user", "question", "customworld", "assignment", "answer"]
        for model in required_models:
            for verb in permission_verbs:
                teacher_group.permissions.add(
                    Permission.objects.get(codename=verb+"_"+model)
                )

        teachers = [{"username": "nicole", "password": "nicole123", "first_name": "Nicole", "last_name": "Tan", "class": ["SSP1", "SSP2"]},
                    {"username": "zhenying", "password": "zhenying123", "first_name": "Zhen Ying", "last_name": "Ngiam", "class": ["BCG1", "BCG2"]}]
        for teacher in teachers:
            created_teacher = User.objects.create_user(username=teacher["username"], password=teacher["password"],
                                                       first_name=teacher["first_name"], last_name=teacher["last_name"],
                                                       is_staff=True)
            teacher_group.user_set.add(created_teacher)

            for class_group in teacher["class"]:
                Class.objects.create(teacher=created_teacher, class_name=class_group)

        self.stdout.write("...teachers created")

    def __create_students(self):
        '''
        Creates 8 Students
        '''
        self.stdout.write("Creating students...")
        students = [
            {"username": "josh", "password": "josh123", "first_name": "Josh", "last_name": "Lim", "class": "SSP1"},
            {"username": "shenrui", "password": "shenrui123", "first_name": "Shen Rui", "last_name": "Chong", "class": "SSP1"},
            {"username": "wanqian", "password": "wanqian123", "first_name": "Wan", "last_name": "Qian", "class": "SSP2"},
            {"username": "tom", "password": "tom123", "first_name": "Tom", "last_name": "Tan", "class": "SSP2"},
            {"username": "mary", "password": "mary123", "first_name": "Mary", "last_name": "Lee", "class": "BCG1"},
            {"username": "jerry", "password": "jerry123", "first_name": "Jerry", "last_name": "Chua", "class": "BCG1"},
            {"username": "ayden", "password": "ayden123", "first_name": "Ayden", "last_name": "Wong", "class": "BCG2"},
            {"username": "jayden", "password": "jayden123", "first_name": "Jayden", "last_name": "Seah", "class": "BCG2"},
            {"username": "james", "password": "james123", "first_name": "James", "last_name": "Barnes", "class": "SSP1"},
            {"username": "sam", "password": "sam123", "first_name": "Sam", "last_name": "Wilson", "class": "BCG1"},
            {"username": "bob", "password": "bob123", "first_name": "Bob", "last_name": "The Builder", "class": "BCG2"},
            {"username": "bob2", "password": "bob123", "first_name": "Bob 2", "last_name": "The Builder", "class": "BCG2"},
            {"username": "bob3", "password": "bob123", "first_name": "Bob 3", "last_name": "The Builder", "class": "BCG2"},
            {"username": "steve", "password": "steve123", "first_name": "Steve", "last_name": "The Builder", "class": "SSP2"}
        ]
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
        world1 = World.objects.create(world_name="Dusza", topic="Requirements Analysis", index=1)
        world2 = World.objects.create(world_name="Wonders", topic="Software Architecture Styles", index=2)
        world3 = World.objects.create(world_name="Zeha", topic="Software Testing", index=3)

        # create sections for world 1
        self.__create_section(world1, "Requirements Elicitation", 1, False)
        self.__create_section(world1, "Conceptual Models", 2, False)
        self.__create_section(world1, "Dynamic Models", 3, True)

        # create sections for world 2
        self.__create_section(world2, "Design Patterns (1)", 4, False)
        self.__create_section(world2, "Design Patterns (2)", 5, False)
        self.__create_section(world2, "MVC", 6, True)

        # create sections for world 3
        self.__create_section(world3, "White Box Testing", 7, False)
        self.__create_section(world3, "Black Box Testing", 8, False)
        self.__create_section(world3, "User Acceptance Testing", 9, True)
        self.stdout.write("...all data for Campaign Mode created")

    def __create_section(self, world, sub_topic_name, index, has_final_boss):
        self.stdout.write("\t...creating section %s" % index)
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
        if world.id == 2: # create demo questions for World 2
            self.__create_demo_questions_and_answers(section)
        else:
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

    def __create_demo_questions_and_answers(self, section):
        """
        Creates Questions for each Section in World 2, with Questions and Answers coming from a CSV file.
        """
        sp_user = User.objects.get(username="junwei")
        if section.index == 4: # section 1 of World 2
            csv_file = open("main/demo_files/section1.csv", encoding="utf-8")
        elif section.index == 5:
            csv_file = open("main/demo_files/section2.csv", encoding="utf-8")
        elif section.index == 6:
            csv_file = open("main/demo_files/section3.csv", encoding="utf-8")
        else:
            self.stdout("Error occured when creating demo questions and answers")
            return

        csv_file.readline() # remove header
        for line in csv_file:
            line = line.strip().split(",")
            question_text = line[0]
            answer1 = line[1]
            answer2 = line[2]
            answer3 = line[3]
            answer4 = line[4]
            correct_answer = line[5]
            difficulty = line[6]

            question = Question.objects.create(section=section, question=question_text, difficulty=difficulty,
                                               created_by=sp_user)

            a1 = Answer.objects.create(question=question, answer=answer1)
            a2 = Answer.objects.create(question=question, answer=answer2)
            a3 = Answer.objects.create(question=question, answer=answer3)
            a4 = Answer.objects.create(question=question, answer=answer4)
            if correct_answer == "1":
                a1.is_correct = True
                a1.save()
            elif correct_answer == "2":
                a2.is_correct = True
                a2.save()
            elif correct_answer == "3":
                a3.is_correct = True
                a3.save()
            elif correct_answer == "4":
                a4.is_correct = True
                a4.save()
            else:
                raise Exception("Error when assigning correct answer")

        csv_file.close()

    def __simulate_students_campaign_mode(self):
        self.stdout.write("Simulating students' playthrough in Campaign Mode...")
        student_records = [
            {"username": "josh", "worlds_finished": 1, "current_section": 3, "current_level": 1, "completed_mode": False},
            {"username": "shenrui", "worlds_finished": 2, "current_section": 3, "current_level": 3, "completed_mode": False},
            {"username": "wanqian", "worlds_finished": 0, "current_section": 2, "current_level": 3, "completed_mode": False},
            {"username": "tom", "worlds_finished": 2, "current_section": 1, "current_level": 2, "completed_mode": False},
            {"username": "mary", "worlds_finished": 1, "current_section": 2, "current_level": 2, "completed_mode": False},
            {"username": "jerry", "worlds_finished": 3, "current_section": 3, "current_level": 3, "completed_mode": True},
            {"username": "ayden", "worlds_finished": 0, "current_section": 1, "current_level": 1, "completed_mode": False},
            # {"username": "jayden", "worlds_finished": 0, "current_section": None, "current_level": None, "completed_mode": False},
            {"username": "james", "worlds_finished": 2, "current_section": 3, "current_level": 2, "completed_mode": False},
            {"username": "sam", "worlds_finished": 3, "current_section": 3, "current_level": 3, "completed_mode": True},
            {"username": "bob", "worlds_finished": 1, "current_section": 3, "current_level": 1, "completed_mode": False},
            {"username": "bob2", "worlds_finished": 1, "current_section": 3, "current_level": 1, "completed_mode": False},
            {"username": "bob3", "worlds_finished": 1, "current_section": 3, "current_level": 1, "completed_mode": False}
        ]

        for student_record in student_records: # should be in order of creation, i.e. josh, shenrui, wanqian, tom, mary, jerry, ayden, jayden
            self.stdout.write("\tSimulating %s's progress..." % student_record["username"])
            student = User.objects.get(username=student_record["username"])
            gm = GameManager(student)

            # get current actual section id to help find actual level id later
            if student_record["worlds_finished"] > 0:
                current_section_id = student_record["worlds_finished"] * 3 + student_record["current_section"]
            else:
                current_section_id = student_record["current_section"]

            current_level_id = (current_section_id-1) * 3 + student_record["current_level"]
            position = gm.get_user_position_in_world()
            if not student_record["completed_mode"]:
                while position.id != current_level_id:
                    position = self.__simulate_answering_questions(gm, position)
            else: # student finished campaign mode
                while True: # simulate until world complete
                    try:
                        position = self.__simulate_answering_questions(gm, position)
                    except PermissionDenied:
                        # denied permission because world is complete. so exit loop
                        break

        self.stdout.write("...finished simulating")

    # for use in __simulate_students_campaign_mode, __simulate_challenge_mode_playthroughs,
    # and __simulate_assignment_playthroughs
    def __simulate_answering_questions(self, gm, position, world=None):
        self.stdout.write("\t...current Level: %s" % position.id)
        questions, session_stats = gm.get_questions(position.section.world)
        question_answer_set = []
        for question in questions:
            question_record = QuestionRecord.objects.get(id=question["record_id"])
            if random.choices(self.answers_boolean,
                              weights=self.correct_answer_prob)[0]: # have to index cause random.choices returns an array
                # answer correctly
                answer = question["answers"].get(is_correct=True)
            else:  # submit random wrong answer
                answer = random.choice(question["answers"].filter(is_correct=False))
            question_answer_set.append({"question_record": question_record, "answer": answer})
        gm.answer_questions(question_answer_set)
        if world:
            return gm.get_user_position_in_world(world)
        return gm.get_user_position_in_world()

    def __create_challenge_mode(self):
        '''
        Creates a Custom World for the 1st 3 Students
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

            # create 4 levels
            for i in range(4):
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
        Creates an Assignment for each of the 2 Teachers for each of their Classes
        '''
        self.stdout.write("Creating Assignments...")

        teachers = User.objects.filter(is_staff=True, is_superuser=False)
        topics = ["Strategy Pattern", "Observer Pattern"]
        for i in range(len(teachers)):
            teacher = teachers[i]
            classes = Class.objects.filter(teacher=teacher)

            # create custom world first
            world_name = "%s's Assignment World" % teacher.first_name
            access_code = teacher.first_name[:3].upper() + "000"
            custom_world = CustomWorld.objects.create(world_name=world_name, topic=topics[i], is_custom_world=True,
                                                      access_code=access_code, created_by=teacher)
            section = Section.objects.create(world=custom_world, sub_topic_name=topics[i])

            # create 4 levels
            for j in range(4):
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
            for class_group in classes:
                Assignment.objects.create(custom_world=custom_world, class_group=class_group, name=topics[i], deadline=self.assignment_deadline)

        self.stdout.write("...assignments created")

    def __simulate_challenge_mode_playthroughs(self):
        play_records = [
            {"username": "josh", "user_world": "shenrui"},
            {"username": "shenrui", "user_world": "wanqian"},
            {"username": "wanqian", "user_world": "josh"},
            {"username": "tom", "user_world": "josh"},
            {"username": "mary", "user_world": "shenrui"},
            {"username": "jerry", "user_world": "wanqian"},
        ]

        self.stdout.write("Simulating Challenge Mode playthroughs...")

        for record in play_records:
            student = User.objects.get(username=record["username"])
            custom_world_owner = User.objects.get(username=record["user_world"])
            custom_world = CustomWorld.objects.get(created_by=custom_world_owner)
            self.stdout.write("\tsimulating %s's progress in %s's challenge world..." % (student.username,
                              custom_world_owner.username))
            gm = GameManager(student)
            position = gm.get_user_position_in_world(custom_world)
            while True:  # simulate until world complete
                try:
                    position = self.__simulate_answering_questions(gm, position, custom_world)
                except PermissionDenied:
                    # denied permission because world is complete. so exit loop
                    break

        self.stdout.write("...finished simulating")

    def __simulate_assignment_playthroughs(self):
        """
        1 Student from each Class will play the Assignment
        """
        self.stdout.write("Simulating Assignment playthroughs...")

        classes = Class.objects.all()
        for class_group in classes:
            student = StudentProfile.objects.filter(class_group=class_group)[0].student
            self.stdout.write("\tsimulating %s's progress in assignment..." % student.username)
            custom_world = Assignment.objects.get(class_group=class_group).custom_world
            gm = GameManager(student)
            position = gm.get_user_position_in_world(custom_world)
            while True:  # simulate until world complete
                try:
                    position = self.__simulate_answering_questions(gm, position, custom_world)
                except PermissionDenied:
                    # denied permission because world is complete. so exit loop
                    break

        self.stdout.write("...finished simulating")

    def __create_demo_challenge_mode(self):
        self.stdout.write("Creating demo Challenge World...")
        student = User.objects.get(username="bob")

        custom_world = CustomWorld.objects.create(world_name="Bob's World", topic="Project Management",
                                                  is_custom_world=True, access_code="BOBBOB", created_by=student)
        section = Section.objects.create(world=custom_world, sub_topic_name="Project Management")

        # create 4 levels
        for i in range(4):
            # create Level
            level_name = "Custom Level " + str(i + 1)
            Level.objects.create(section=section, level_name=level_name)

        # create 12 Questions
        csv_file = open("main/demo_files/challenge.csv", encoding="utf-8")
        csv_file.readline() # get rid of header
        for line in csv_file:
            line = line.strip().split(",")
            question_text = line[0]
            answer1 = line[1]
            answer2 = line[2]
            answer3 = line[3]
            answer4 = line[4]
            correct_answer = line[5]

            question = Question.objects.create(section=section, question=question_text, difficulty="1",
                                               created_by=student)

            a1 = Answer.objects.create(question=question, answer=answer1)
            a2 = Answer.objects.create(question=question, answer=answer2)
            a3 = Answer.objects.create(question=question, answer=answer3)
            a4 = Answer.objects.create(question=question, answer=answer4)
            if correct_answer == "1":
                a1.is_correct = True
                a1.save()
            elif correct_answer == "2":
                a2.is_correct = True
                a2.save()
            elif correct_answer == "3":
                a3.is_correct = True
                a3.save()
            elif correct_answer == "4":
                a4.is_correct = True
                a4.save()
            else:
                raise Exception("Error when assigning correct answer when making Challenge World")

        csv_file.close()

    def __create_demo_assignment(self):
        self.stdout.write("Creating demo Assignment World...")
        teacher = User.objects.get(username="nicole")

        # create custom world first
        custom_world = CustomWorld.objects.create(world_name="UML Proficiency Test", topic="UML Diagrams",
                                                  is_custom_world=True, access_code="UMLUML", created_by=teacher)
        section = Section.objects.create(world=custom_world, sub_topic_name="UML Diagrams")

        # create 4 levels
        for j in range(4):
            # create Level
            level_name = "Assignment Level " + str(j + 1)
            Level.objects.create(section=section, level_name=level_name)

        # create 12 Questions
        csv_file = open("main/demo_files/assignment.csv", encoding="utf-8")
        csv_file.readline()  # get rid of header
        for line in csv_file:
            line = line.strip().split(",")
            question_text = line[0]
            answer1 = line[1]
            answer2 = line[2]
            answer3 = line[3]
            answer4 = line[4]
            correct_answer = line[5]

            question = Question.objects.create(section=section, question=question_text, difficulty="1",
                                               created_by=teacher)

            a1 = Answer.objects.create(question=question, answer=answer1)
            a2 = Answer.objects.create(question=question, answer=answer2)
            a3 = Answer.objects.create(question=question, answer=answer3)
            a4 = Answer.objects.create(question=question, answer=answer4)
            if correct_answer == "1":
                a1.is_correct = True
                a1.save()
            elif correct_answer == "2":
                a2.is_correct = True
                a2.save()
            elif correct_answer == "3":
                a3.is_correct = True
                a3.save()
            elif correct_answer == "4":
                a4.is_correct = True
                a4.save()
            else:
                raise Exception("Error when assigning correct answer when making Challenge World")

        # create assignment
        class_group = Class.objects.get(class_name="BCG2")
        Assignment.objects.create(custom_world=custom_world, class_group=class_group, name="UML Assignment",
                                  deadline=self.assignment_deadline)

        csv_file.close()

    def __simulate_demo_steve(self):
        """
        Steve will finish 1 Level of the first World. For that level he will get 2 Easy Correct and 1 Easy Wrong
        So he would be at 15 points, after which answering the next question correctly will grant him Medium difficulty
        """
        self.stdout.write("Simulating steve's progress...")
        steve = User.objects.get(username="steve")

        question = Question.objects.get(id=1)
        QuestionRecord.objects.create(user=steve, question=question, level_id=1, is_correct=True, points_change=10,
                                      reason="Correct")
        question = Question.objects.get(id=2)
        QuestionRecord.objects.create(user=steve, question=question, level_id=1, is_correct=True, points_change=10,
                                      reason="Correct")
        question = Question.objects.get(id=3)
        QuestionRecord.objects.create(user=steve, question=question, level_id=1, is_correct=False, points_change=-5,
                                      reason="Incorrect")

        UserLevelProgressRecord.objects.create(user=steve, level_id=1, is_completed=True, completed_time=timezone.now())
        UserLevelProgressRecord.objects.create(user=steve, level_id=2)
        self.stdout.write("...finished simulating")