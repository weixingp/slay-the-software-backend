from random import randint

from rest_framework.exceptions import PermissionDenied

from main.models import UserLevelProgressRecord, UserWorldProgressRecord, World, Level, Section, Question, \
    QuestionRecord, Answer


class GameManager:
    def __init__(self, user):
        self.user = user

    # Should change it for custom map
    def get_user_position_in_map(self):
        position = UserWorldProgressRecord.objects.filter(user=self.user, is_completed=False)

        # Instantiate the user position to the first world
        if not position:
            world = World.objects.all.order_by("index")[0]
            position = UserWorldProgressRecord.objects.create(
                user=self.user,
                world=world,
            )
        else:
            position = position[0]

        return position.world

    def get_user_position_in_world(self):
        position = UserLevelProgressRecord.objects.filter(user=self.user, is_completed=False)

        # Instantiate the user position to the first level
        if not position:
            level = Level.objects.all().order_by("id")[0]
            position = UserLevelProgressRecord.objects.create(
                user=self.user,
                level=level,
            )
        else:
            position = position[0]

        return position.level

    def check_access_to_level(self, level_id):
        self.get_user_position_in_map()  # Put here first to set user location
        curr_position = self.get_user_position_in_world()

        if level_id == curr_position.id:
            return curr_position
        else:
            return False

    def get_user_points_by_world(self, world_id):
        return 1

    def new_question_record_session(self, level, question):
        record = QuestionRecord.objects.filter(
            user=self.user,
            level=level,
            is_completed=False
        )

        # Only generate a new session if there is no unanswered question in the world
        if not record:
            record = QuestionRecord.objects.create(
                user=self.user,
                level=level,
                question=question,
            )
        else:
            record = record[0]
        return record

    def get_question_answer_in_main_world(self):
        position = self.get_user_position_in_world()

        section = position.section
        easy_qn_threshold = 14
        normal_qn_threshold = 30
        points = self.get_user_points_by_world(section.world.id)
        # 1 -> Easy, 2 -> Normal, 3 -> Hard
        if points <= easy_qn_threshold:
            difficulty = "1"
        elif points <= normal_qn_threshold:
            difficulty = "2"
        else:
            difficulty = "3"

        # Get answered questions of user.
        answered_question = QuestionRecord.objects \
            .filter(user=self.user, is_correct=True) \
            .values_list('question_id', flat=True)

        # Exclude the answered questions
        pks = Question.objects.filter(
            section=section,
            difficulty=difficulty
        ).exclude(
            id__in=list(answered_question)
        ).values_list('pk', flat=True)

        if len(pks) < 1:
            pks = Question.objects.filter(section=section, difficulty=difficulty).values_list('pk', flat=True)

        # Get random question of the processed list of questions
        random_idx = randint(0, len(pks) - 1)
        random_qn = Question.objects.get(pk=pks[random_idx])

        # Add to question record
        record = self.new_question_record_session(position, random_qn)
        question = record.question

        # Get the answer for this question
        answer = Answer.objects.filter(question=question)

        return question, answer, record
