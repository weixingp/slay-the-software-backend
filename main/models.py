from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User
from django.db import models
from django.utils import timezone


# Create your models here.
class Question(models.Model):
    question = models.TextField(max_length=1000)
    # world_id = models.ForeignKey(World, on_delete=models.CASCADE, related_name="question_world_fk")
    DIFFICULTY_CHOICES = (
        ("1", "Easy"),
        ("2", "Normal"),
        ("3", "Hard"),
    )
    difficulty = models.CharField(
        max_length=1,
        choices=DIFFICULTY_CHOICES,
    )

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="question_user_fk")
    time_created = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return self.question


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answer_question_fk")
    answer = models.CharField(max_length=256)
    is_correct = models.BooleanField(default=False)

    # Object name for display in admin panel
    def __str__(self):
        if self.is_correct:
            return "Correct"
        else:
            return "Incorrect"

class User(models.Model):
    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)
    username = models.CharField(max_length=256)
    email = models.EmailField(max_length=254)
    password = models.CharField(max_length=256)
    is_superuser = models.BooleanField()
    is_teacher = models.BooleanField()
    is_active = models.BooleanField()
    date_joined = models.DateField(auto_now=True)

    def __str__(self):
        return self.first_name + " " + self.last_name

class QuestionRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="questionrecord_user_fk")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="questionrecord_question_fk")
    score_change = models.IntegerField()
    reason = models.CharField(max_length=256)
    time = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.question.question, self.score_change)

class UserWorldProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userworldprogressrecord_user_fk")
    world = models.ForeignKey(World, on_delete=models.SET_NULL, related_name="userworldprogressrecord_world_fk")
    is_completed = models.BooleanField(default=False)
    started_time = models.DateTimeField(auto_now=True)
    completed_time = models.DateTimeField(auto_now=False)

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.world.world_name, self.is_completed)

class UserLevelProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="userlevelprogressrecord_user_fk")
    level = models.ForeignKey(Level, on_delete=models.SET_NULL, related_name="userlevelprogressrecord_level_fk")
    is_completed = models.BooleanField(default=False)
    started_time = models.DateTimeField(auto_now=True)
    completed_time = models.DateTimeField(auto_now=False)

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.level.level_name, self.is_completed)