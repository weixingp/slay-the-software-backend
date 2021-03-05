from random import randint

from django.utils.timezone import now
from rest_framework.exceptions import PermissionDenied, NotFound

from main.models import UserLevelProgressRecord, UserWorldProgressRecord, World, Level, Section, Question, \
    QuestionRecord, Answer


class GameManager:
    difficulty_points_map = {  # Getting correct answer
        True: {
            "1": 1,
            "2": 2,
            "3": 3,
        },
        False: {  # Getting wrong answer
            "1": -0.5,
            "2": -1,
            "3": -2,
        }

    }

    def __init__(self, user):
        self.user = user

    # Should change it for custom map
    def get_user_position_in_map(self):
        pass
        # position = UserWorldProgressRecord.objects.filter(user=self.user, is_completed=False)
        #
        # # Instantiate the user position to the first world
        # if not position:
        #     world = World.objects.all.order_by("index")[0]
        #     position = UserWorldProgressRecord.objects.create(
        #         user=self.user,
        #         world=world,
        #     )
        # else:
        #     position = position[0]
        #
        # return position.world

    def instantiate_position(self, world=None):
        # Sets the initial location

        if not world:
            level = Level.objects.filter(
                section__world__is_custom_world=False
            ).order_by('id')[0]
        else:
            level = Level.objects.filter(
                section__world=world
            ).order_by('id')[0]

        UserLevelProgressRecord.objects.create(
            user=self.user,
            level=level,
        )

        return level

    def get_user_position_in_world(self, world=None):
        if not world or not world.is_custom_world:
            # Progress in main world
            progress = UserLevelProgressRecord.objects.filter(
                user=self.user,
                level__section__world__is_custom_world=False
            )
        else:
            # Progress in custom world
            progress = UserLevelProgressRecord.objects.filter(
                user=self.user,
                level__section__world=world
            )

        # Instantiate the user position to the first level
        a = progress.filter(is_completed=False)

        b = progress.filter(is_completed=True)

        if not progress:
            # User doesn't have any record at all
            position = self.instantiate_position(world)
        elif not a and b:
            # User has finished the main worlds / custom world
            position = progress.order_by('-id')[0].level  # Last position
        else:
            position = a[0].level

        return position

    def check_access_to_level(self, level_id):
        self.get_user_position_in_map()  # Put here first to set user location
        curr_position = self.get_user_position_in_world()

        if level_id == curr_position.id:
            return curr_position
        else:
            return False

    def get_user_points_by_world(self, world):
        # To be implemented
        return 1

    def new_question_record_session(self, level, question):
        record = QuestionRecord.objects.filter(
            user=self.user,
            level=level,
        )

        # Only generate a new session if there is no unanswered question in the world
        if not record:
            # Only generate a new session if there is a
            record = QuestionRecord.objects.create(
                user=self.user,
                level=level,
                question=question,
            )
        else:
            record = record[0]
            if record.is_completed:
                # User has completed the main worlds / custom world
                record = None
        return record

    def unlock_level(self, world=None):
        position = self.get_user_position_in_world(world)
        levels = Level.objects.filter(id__gt=position.id, section=position.section).order_by('id')
        if not levels:
            if not world:
                # Try the next section
                next_section = Section.objects.filter(id__gt=position.section.id, world__is_custom_world=False)
                if not next_section:
                    # Try the next world
                    next_world = World.objects.filter(id__gt=position.section.world.id, is_custom_world=False)
                    if not next_world:
                        # User has finished the main world
                        return None
                    else:
                        next_section = Section.objects.filter(world=next_world[0]).order_by('id')[0]
                else:
                    next_section = next_section[0]

                next_level = Level.objects.filter(section=next_section).order_by('id')[0]
            else:
                # User has finished the custom world
                return None
        else:
            next_level = levels[0]

        UserLevelProgressRecord.objects.create(
            user=self.user,
            level=next_level,
        )

        return next_level

    def check_answer_in_world(self, world, answer):
        if world is None:
            # Main world
            record = QuestionRecord.objects.filter(
                user=self.user,
                level__section__world__is_custom_world=False,
                is_completed=False
            )
        else:
            # Custom world
            record = QuestionRecord.objects.filter(
                user=self.user,
                level__section__world=world,
                is_completed=False
            )

        if not record:
            raise PermissionDenied(detail="You are not allowed to check answer.")
        else:
            record = record[0]

        if answer.question.id != record.question.id:
            raise PermissionDenied(detail="You are not allowed to check this answer.")

        # Update the question record
        record.is_completed = True
        record.points_change = self.difficulty_points_map[answer.is_correct][record.question.difficulty]
        record.completed_time = now()
        record.is_correct = answer.is_correct
        record.save()

        # Update player progress
        progress = UserLevelProgressRecord.objects.get(level=record.level)
        progress.is_completed = True
        progress.completed_time = now()
        progress.save()

        # Unlock the next level
        self.unlock_level()
        return record.is_correct, record.points_change

    def get_question_answer_in_main_world(self, world):
        position = self.get_user_position_in_world(world)

        section = position.section
        easy_qn_threshold = 14
        normal_qn_threshold = 30
        points = self.get_user_points_by_world(section.world)
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
            # Recycle questions that has been unanswered
            pks = Question.objects.filter(section=section, difficulty=difficulty).values_list('pk', flat=True)
            if len(pks) < 1:
                # Choose from all difficulties
                pks = Question.objects.filter(
                    section=section,
                    difficulty__in=self.difficulty_points_map[True].keys()
                ).values_list('pk', flat=True)

        if len(pks) < 1:
            # If still no question, raise
            raise NotFound(detail="No question found for this world.")

        # Get random question of the processed list of questions
        random_idx = randint(0, len(pks) - 1)
        random_qn = Question.objects.get(pk=pks[random_idx])

        # Add to question record
        record = self.new_question_record_session(position, random_qn)
        if not record:
            raise PermissionDenied(detail="You are not allowed to get question. World completed.")
        question = record.question

        # Get the answer for this question
        answer = Answer.objects.filter(question=question)

        return question, answer, record
