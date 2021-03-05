from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User
from django.db import models
from django.utils import timezone


# Create your models here.
class World(models.Model):
    world_name = models.CharField(max_length=64)
    topic = models.CharField(max_length=64)
    is_custom_world = models.BooleanField(default=False)
    index = models.IntegerField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.world_name, self.topic)


class Section(models.Model):
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="sections")
    sub_topic_name = models.CharField(max_length=30)
    index = models.IntegerField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.world_id, self.sub_topic_name)


class Question(models.Model):
    question = models.TextField(max_length=1000)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="questions", blank=True, null=True)
    DIFFICULTY_CHOICES = (
        ("1", "Easy"),
        ("2", "Normal"),
        ("3", "Hard"),
    )
    difficulty = models.CharField(
        max_length=1,
        choices=DIFFICULTY_CHOICES,
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_questions", blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return self.question


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    answer = models.CharField(max_length=256)
    is_correct = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        if self.is_correct:
            return "Correct"
        else:
            return "Incorrect"


class CustomWorld(World):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="custom_worlds")
    access_code = models.CharField(max_length=256) # to change max length after format has been decided
    is_active = models.BooleanField()
    # date_created = models.DateTimeField(auto_now_add=True)
    # date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.world_id, self.created_by)


class Assignment(models.Model):
    custom_world = models.OneToOneField(CustomWorld, on_delete=models.CASCADE, primary_key=True)
    class_index = models.CharField(max_length=30)
    name = models.CharField(max_length=30)
    deadline = models.DateTimeField(auto_now=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.custom_world, self.class_index)


class Level(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="levels")
    level_name = models.CharField(max_length=64)
    is_boss_level = models.BooleanField(default=False)
    is_final_boss_level = models.BooleanField(default=False)
    index = models.IntegerField(unique=True)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.section_id, self.level_name)


# class LevelPath(models.Model):
#     from_level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="levelpath_fromlevel_fk")
#     to_level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="levelpath_tolevel_fk")
#     date_created = models.DateTimeField(auto_now_add=True)
#     date_modified = models.DateTimeField(auto_now=True)
#
#     def __str__(self):
#         return "%s|%s" % (self.from_level, self.to_level)


# Points system migrated to UserLevelProgressRecord
class QuestionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questionrecord_user_fk")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="questionrecord_question_fk")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="questionrecord_level_fk")
    is_correct = models.BooleanField(null=True, blank=True)
    points_change = models.IntegerField(default=0)
    reason = models.CharField(max_length=256, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completed_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.question.question, self.points_change)


class UserWorldProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userworldprogressrecord_user_fk")
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="userworldprogressrecord_world_fk")
    is_completed = models.BooleanField(default=False)
    started_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(null=True, blank=True)

    unique_together = [['user', 'world']]

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.world.world_name, self.is_completed)


class UserLevelProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userlevelprogressrecord_user_fk")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="userlevelprogressrecord_level_fk")
    is_completed = models.BooleanField(default=False)
    started_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(null=True, blank=True)

    unique_together = [['user', 'level']]

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.level.level_name, self.is_completed)
