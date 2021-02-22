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

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="question_world_fk")
    time_created = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return self.question


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="question_fk")
    answer = models.CharField(max_length=256)
    is_correct = models.BooleanField(default=False)

    # Object name for display in admin panel
    def __str__(self):
        if self.is_correct:
            return "Correct"
        else:
            return "Incorrect"
