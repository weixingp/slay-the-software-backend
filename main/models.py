from urllib import parse

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, User, Group
from django.db import models
from django.db.models import CharField
from django.forms import forms
from django.utils import timezone
from django.utils.safestring import mark_safe

from main.validators import validate_matric
from django.utils.translation import ugettext_lazy as _


class MatriculationField(CharField):
    def __init__(self, *args, **kwargs):
        super(MatriculationField, self).__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super(MatriculationField, self).clean(*args, **kwargs)

        matric = data.upper().strip()

        try:
            check = validate_matric(matric)
        except Exception:
            raise forms.ValidationError(_('Wrong matric number format, please double check.'))

        if not check:
            raise forms.ValidationError(_('Invalid matric number, please double check.'))

        return matric


# Create your models here.
class World(models.Model):
    world_name = models.CharField(max_length=64)
    topic = models.CharField(max_length=64)
    is_custom_world = models.BooleanField(default=False)
    index = models.IntegerField(unique=True, null=True, default=None)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.world_name, self.topic)


class Section(models.Model):
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="sections")
    sub_topic_name = models.CharField(max_length=30)
    index = models.IntegerField(unique=True, null=True, default=None)
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

    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="created_questions", blank=True,
                                   null=True)
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
    access_code = models.CharField(max_length=6, unique=True)
    is_active = models.BooleanField(default=True)

    # date_created = models.DateTimeField(auto_now_add=True)
    # date_modified = models.DateTimeField(auto_now=True)

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.world_name, self.created_by)

    class Meta:
        verbose_name = 'Custom World'
        verbose_name_plural = 'Custom Worlds'


class Class(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="classes")
    class_name = models.CharField(max_length=30)

    def __str__(self):
        return self.class_name


class Assignment(models.Model):
    custom_world = models.ForeignKey(CustomWorld, on_delete=models.CASCADE)
    class_group = models.ForeignKey(Class, on_delete=models.CASCADE, related_name="assignments")
    name = models.CharField(max_length=30)
    deadline = models.DateTimeField(auto_now=False)
    date_created = models.DateTimeField(auto_now_add=True)
    date_modified = models.DateTimeField(auto_now=True)

    unique_together = [['custom_world', 'class_group']]

    # Object name for display in admin panel
    def __str__(self):
        return "%s|%s" % (self.custom_world, self.class_group)

    def get_twitter_share_btn(self):
        base_url = "https://cz3003.kado.sg/share/?code="
        share_url = base_url + self.custom_world.access_code
        share_url_encoded = parse.quote(share_url)

        html = """
        <a 
        href="https://twitter.com/share?ref_src=twsrc%5Etfw" 
        class="twitter-share-button" 
        data-size="large" 
        data-text="Hi students, new Slay the Software assignment is out. Please complete it before the deadline: 
        - Topic: """ + self.custom_world.topic + """
        - Access Code: """ + self.custom_world.access_code + """  " 
        data-url=" """ + share_url + """ " 
        data-lang="en" 
        data-show-count="false">Tweet
        </a>
        <script async src="https://platform.twitter.com/widgets.js" charset="utf-8">
        </script>
        """
        return mark_safe(html)

    def get_fb_share_btn(self):
        base_url = "https://cz3003.kado.sg/share/?code="
        share_url = base_url + self.custom_world.access_code
        share_url_encoded = parse.quote(share_url)

        html = """
        <div
        class="fb-share-button" 
        data-href=" """ + share_url + """ " 
        data-layout="button" data-size="large">
            <a target="_blank" 
            href="https://www.facebook.com/sharer/sharer.php?u=""" + share_url_encoded + """;src=sdkpreparse" 
            class="fb-xfbml-parse-ignore">Share
            </a>
        </div>
        """
        return mark_safe(html)

    get_fb_share_btn.short_description = 'Share to FB'
    get_twitter_share_btn.short_description = 'Share to Twitter'


class Level(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="levels")
    level_name = models.CharField(max_length=64)
    is_boss_level = models.BooleanField(default=False)
    is_final_boss_level = models.BooleanField(default=False)
    index = models.IntegerField(unique=True, null=True, default=None)
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_question_records")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="question_records")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="level_question_records")
    is_correct = models.BooleanField(null=True, blank=True)
    points_change = models.IntegerField(default=0)
    reason = models.CharField(max_length=256, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    completed_time = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.question.question, self.points_change)


class UserWorldProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="world_progress_record")
    world = models.ForeignKey(World, on_delete=models.CASCADE, related_name="user_progress_record")
    is_completed = models.BooleanField(default=False)
    started_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(null=True, blank=True)

    unique_together = [['user', 'world']]

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.world.world_name, self.is_completed)


class UserLevelProgressRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="level_progress_record")
    level = models.ForeignKey(Level, on_delete=models.CASCADE, related_name="user_progress_record")
    is_completed = models.BooleanField(default=False)
    started_time = models.DateTimeField(auto_now_add=True)
    completed_time = models.DateTimeField(null=True, blank=True)

    unique_together = [['user', 'level']]

    def __str__(self):
        return "%s|%s|%s" % (self.user.first_name, self.level.level_name, self.is_completed)


class StudentProfile(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")
    year_of_study = models.IntegerField()
    class_group = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True, related_name="students")
    has_reset_password = models.BooleanField(default=False)

    def __str__(self):
        return self.student.first_name + " " + self.student.last_name + "|" + self.class_group.class_name