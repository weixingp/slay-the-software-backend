from django.db.models import Sum, Avg
from main.models import Section, Level, StudentProfile, Class, QuestionRecord, Question, User


def filter_question_records_by_class(class_name, question_records):
    class_group = Class.objects.get(class_name=class_name)
    students = [student_profile.student for student_profile in
                StudentProfile.objects.filter(class_group=class_group)]
    return question_records.filter(user__in=students)


def remove_inactive_students(question_records):
    active_students = User.objects.filter(is_staff=False, is_superuser=False, is_active=True)
    return question_records.filter(user__in=active_students)


def calculate_world_statistics(world, class_name=None):
    """
    Calculates for each Section in the given World:
    - total points in the Section
    - average points in the Section
    - for each Question in the Section, the number of correct and incorrect attempts
    """
    sections = Section.objects.filter(world=world)
    sections_stats = []
    for section in sections:
        # calculate total and avg points
        levels = Level.objects.filter(section=section)
        question_records = QuestionRecord.objects.filter(level__in=levels)
        question_records = remove_inactive_students(question_records)

        # retrieve stats of students in given class, if any
        if class_name:
            question_records = filter_question_records_by_class(class_name, question_records)

        if len(question_records) == 0:
            avg_points = 0
            total_points = 0
        else:
            avg_points = round(question_records.aggregate(Avg('points_change'))["points_change__avg"], 2)
            total_points = question_records.aggregate(Sum('points_change'))["points_change__sum"]

        # get stats for each question in the section
        questions_stats = []
        questions = Question.objects.filter(section=section)
        for question in questions:
            question_record = QuestionRecord.objects.filter(question=question)
            question_record = remove_inactive_students(question_record)

            # retrieve stats of students in given class, if any
            if class_name:
                question_record = filter_question_records_by_class(class_name, question_record)

            num_correct = len(question_record.filter(is_correct=True))
            num_incorrect = len(question_record.filter(is_correct=False))
            questions_stats.append({
                "question": question.question,
                "num_correct": num_correct,
                "num_incorrect": num_incorrect,
            })

        sections_stats.append({
            "sub_topic_name": section.sub_topic_name,
            "avg_points": avg_points,
            "total_points": total_points,
            "questions": questions_stats
        })

    return {"world_name": world.world_name, "sections": sections_stats}
