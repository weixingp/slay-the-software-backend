import random
from math import ceil
from random import randint

from django.db.models import Sum
from django.utils.timezone import now
from rest_framework.exceptions import PermissionDenied, NotFound, ValidationError

from main.models import UserLevelProgressRecord, UserWorldProgressRecord, World, Level, Section, Question, \
    QuestionRecord, Answer


class GameManager:
    difficulty_points_map = {  # Getting correct answer
        True: {
            "1": 10,
            "2": 20,
            "3": 30,
        },
        False: {  # Getting wrong answer
            "1": -5,
            "2": -10,
            "3": -15,
        }

    }

    boss_level_qn = 10  # Should not be changed after the game has been init
    normal_level_qn = 3  # Should not be changed after the game has been init

    def __init__(self, user):
        self.user = user

    def __instantiate_position(self, world=None):
        # Sets the initial location

        if not world or not world.is_custom_world:
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
            position = self.__instantiate_position(world)
        elif not a and b:
            # User has finished the main worlds / custom world
            position = progress.order_by('-id')[0].level  # Last position
        else:
            position = a[0].level

        return position

    def get_user_points_by_world(self, world):
        if not world:
            position = self.get_user_position_in_world()
            world = position.section.world

        records = QuestionRecord.objects.filter(
            user=self.user,
            level__section__world=world,
        )
        if not records:
            points = 0
        else:
            points = records.aggregate(Sum('points_change'))
            points = points['points_change__sum']
        return points

    def get_qn_difficulty_by_world(self, world):
        if not world:
            position = self.get_user_position_in_world()
            world = position.section.world

        easy_qn_threshold = 20
        normal_qn_threshold = 65

        points = self.get_user_points_by_world(world)
        # 1 -> Easy, 2 -> Normal, 3 -> Hard
        if points <= easy_qn_threshold:
            difficulty = "1"
        elif points <= normal_qn_threshold:
            difficulty = "2"
        else:
            difficulty = "3"

        return difficulty

    def __new_boss_question_record_session(self, level, questions):
        records = QuestionRecord.objects.filter(
            user=self.user,
            level=level,
        )

        completed = records.filter(is_completed=True)
        uncompleted = records.filter(is_completed=False)

        if completed and uncompleted:
            raise ValidationError(detail="Database data mismatch, please contact Admin.")

        progress = UserLevelProgressRecord.objects.filter(
            user=self.user,
            level=level,
            is_completed=False
        )
        if not progress:
            raise PermissionDenied(detail="You are not allowed to get questions, world completed.")

        record_list = []
        if not uncompleted:
            for question in questions:
                record = QuestionRecord.objects.create(
                    user=self.user,
                    level=level,
                    question=question,
                )
                record_list.append(record)
            return record_list
        else:
            return records

    def __new_question_record_session(self, level, question):
        records = QuestionRecord.objects.filter(
            user=self.user,
            level=level,
        )

        if not records:
            # Only generate a new session if there is no unanswered question in the world
            record = QuestionRecord.objects.create(
                user=self.user,
                level=level,
                question=question,
            )
        else:
            # Uncompleted question for this level
            records = records.filter(is_completed=False)
            if records:
                record = records[0]
            else:
                progress = UserLevelProgressRecord.objects.filter(
                    user=self.user,
                    level=level,
                    is_completed=False
                )
                if progress:
                    # Generate a question session if there is uncompleted progress for this level
                    record = QuestionRecord.objects.create(
                        user=self.user,
                        level=level,
                        question=question,
                    )
                else:
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
                    print(next_world)
                    if not next_world:
                        # User has finished the main world
                        return None
                    else:
                        next_section = Section.objects.filter(world=next_world[0]).order_by('id')
                        if next_section:
                            next_world = next_world[0]
                        else:
                            # World is empty :(
                            return None
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

    def __check_answer(self, question, answer):
        if answer.question != question:
            raise PermissionDenied(detail="One or more answers does not belong to their respective question.")

        return answer.is_correct

    def __award_points(self, question_record, is_correct, points):
        """
        :param question_record: The question record object
        :param points: Points change
        :return: Nothing

        Sets the points for answering question and marks the question record completed
        """
        question_record.is_completed = True
        question_record.points_change = points
        question_record.completed_time = now()
        question_record.is_correct = is_correct
        question_record.save()

    def __complete_level(self, level):
        """
        Completes the current level and unlock the next level if any.
        :param level: the level object
        :return:
        """
        progress = UserLevelProgressRecord.objects.get(
            user=self.user,
            level=level,
        )
        progress.is_completed = True
        progress.completed_time = now()
        progress.save()

        # Unlock the next level
        self.unlock_level()

    def answer_questions(self, question_answer_set):

        temp_qr = question_answer_set[0]["question_record"]

        if not temp_qr.level.is_final_boss_level:
            # Answer checking for normal level
            if len(question_answer_set) != 1:
                raise ValidationError(detail="Only one question can be checked at a time for normal levels.")

            item = question_answer_set[0]
            qr = item["question_record"]

            is_correct, points = self.__check_normal_level_answer(qr, item['answer'])
            # Award the points
            self.__award_points(qr, is_correct, points)

            qn_index = self.__get_question_index(qr.level)
            if qn_index == self.normal_level_qn:
                # Unlock the next level
                self.__complete_level(qr.level)

            res = [{
                "record_id": qr.id,
                "question_text": qr.question.question,
                "is_correct": is_correct,
                "points": points
            }]

            return res
        else:
            # Answer checking for boss level
            if len(question_answer_set) != self.boss_level_qn:
                raise ValidationError(detail=f"{self.boss_level_qn} answers needed for final boss level.")

            unanswered_records = QuestionRecord.objects.filter(
                user=self.user,
                is_completed=False
            )

            if len(unanswered_records) != self.boss_level_qn:
                raise ValidationError(detail="Question record data mismatch! Contact admin immediately")

            # Answer checking for boss level
            correct_counter = 0
            res = []
            level = question_answer_set[0]["question_record"].level
            for item in question_answer_set:
                qr = item["question_record"]

                is_correct = self.__check_boss_level_answer(qr, item['answer'])
                correct_counter += 1 if is_correct else 0
                temp = {
                    "record_id": qr.id,
                    "question_text": qr.question.question,
                    "is_correct": is_correct,
                    "points": 0
                }
                res.append(temp)

            index = 0
            # This is to ensure atomicity of data
            for item in question_answer_set:
                self.__award_points(item["question_record"], res[index]["is_correct"], res[index]["points"])
                index += 1

            # Must answer at least 5 questions correctly.
            if correct_counter > 5:
                # Unlock the next level
                self.__complete_level(level)
            return res

    def __check_normal_level_answer(self, question_record, answer):

        is_correct = self.__check_answer(question_record.question, answer)
        # Points change
        curr_points = self.get_user_points_by_world(question_record.level.section.world)
        points = self.difficulty_points_map[is_correct][question_record.question.difficulty]

        # Do not let points fall below 0
        if curr_points + points < 0:
            points = -curr_points

        return is_correct, points

    def __check_boss_level_answer(self, question_record, answer):
        return self.__check_answer(question_record.question, answer)

    def __get_question_index(self, position):
        qr = QuestionRecord.objects.filter(
            user=self.user,
            level=position,
        )

        return len(qr)

    def __get_single_question_set(self, position):
        qn_index = self.__get_question_index(position)

        if qn_index > self.normal_level_qn - 1:
            raise PermissionDenied(detail="You are not allowed to get more questions of this level.")

        section = position.section

        difficulty = self.get_qn_difficulty_by_world(section.world)

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
        record = self.__new_question_record_session(position, random_qn)
        if not record:
            raise PermissionDenied(detail="You are not allowed to get question. World completed.")
        question = record.question

        # Get the answer for this question
        answers = Answer.objects.filter(question=question)
        res = [{
            "question": question,
            "answers": answers,
            "record_id": record.id,
            "index": qn_index,
        }]
        return res

    def __get_boss_level_question_answer(self, position):
        total_qn = self.boss_level_qn
        section_list = list(Section.objects.filter(world=position.section.world).values_list('id', flat=True))
        # Get answered questions of user.
        answered_question = QuestionRecord.objects \
            .filter(user=self.user, is_correct=True) \
            .values_list('question_id', flat=True)

        pks = Question.objects \
            .filter(section__id__in=section_list) \
            .exclude(id__in=list(answered_question)) \
            .values_list('pk', flat=True)
        pks = list(pks)

        # If unanswered question is less than 10
        if len(pks) < total_qn:
            diff = total_qn - len(pks)
            all_pks = Question.objects \
                .filter(section__id__in=section_list) \
                .values_list('pk', flat=True)

            # If not enough questions
            if len(all_pks) < 1:
                raise NotFound(detail="No question found for this world.")
            elif len(all_pks) < total_qn:
                to_add = random.choices(all_pks, k=diff)  # Random id with replacement
            else:
                to_add = random.sample(all_pks, k=diff)  # Random id without replacement

            pks += to_add

        random_qns = []
        random_ids = random.sample(pks, k=total_qn)
        for qn_id in random_ids:
            qn = Question.objects.get(pk=qn_id)
            random_qns.append(qn)

        records = self.__new_boss_question_record_session(level=position, questions=random_qns)
        res = []
        for item in records:
            question = item.question
            answers = Answer.objects.filter(question=question)
            temp = {
                "question": question,
                "answers": answers,
                "record_id": item.id,
                "index": None
            }
            res.append(temp)
        return res

    def get_questions(self, world):
        position = self.get_user_position_in_world(world)
        if position.is_final_boss_level:
            question_list = self.__get_boss_level_question_answer(position)
        else:
            question_list = self.__get_single_question_set(position)

        return question_list
