from django.contrib import admin
from django.db.models import Sum, Avg
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.urls import path
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from rest_framework.authtoken.models import Token


# Register your models here.

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student', 'year_of_study', 'class_group', 'has_reset_password')
    list_filter = ('class_group', )
    search_fields = ('student__email', 'student__username',)


class ProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = True
    verbose_name_plural = 'Profile'
    fk_name = 'student'


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)


class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('custom_world', 'class_group', 'name', 'deadline', 'date_created', 'date_modified',)
    list_filter = ('class_group',)


class AnswerAdmin(admin.TabularInline):
    model = Answer


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'section', 'difficulty', 'created_by', 'date_created', 'date_modified',)
    list_filter = ('section', 'difficulty', 'created_by',)
    exclude = ['created_by', ]
    inlines = [AnswerAdmin, ]


class CustomWorldAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'access_code', 'is_active',)

class SectionAdmin(admin.ModelAdmin):
    list_display = ('sub_topic_name', 'index', 'world_id',)

class WorldAdmin(admin.ModelAdmin):
    list_display = ('world_name', 'topic', 'is_custom_world', 'index',)

class LevelAdmin(admin.ModelAdmin):
    list_display = ('level_name', 'is_boss_level', 'is_final_boss_level', 'section_id',)

class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        app_list += [
            {
                "name": "Full Statistics",
                "app_label": "main",
                # "app_url": "/admin/test_view",
                "models": [
                    {
                        "name": "Campaign Mode",
                        "object_name": "TestModel",
                        "admin_url": "/admin/campaign_statistics/",
                        "view_only": True,
                    },
                    {
                        "name": "Assignments",
                        "object_name": "TestModel",
                        "admin_url": "/admin/assignment_statistics",
                        "view_only": True,
                    },
                ],
            }
        ]
        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('campaign_statistics/', self.admin_view(self.campaign_statistics_view)),
            path('campaign_statistics/<str:class_name>/', self.admin_view(self.campaign_statistics_view)),
            # path('assignment_statistics/', self.admin_view(self.assignment_statistics_view)),
            path('import-users/', self.admin_view(self.import_user_view))
        ]
        return custom_urls + urls

    def import_user_view(self, request, class_name=None):
        template = loader.get_template('admin/import-users.html')

        context = {

        }

        response = HttpResponse(template.render(context, request))
        return response

    def campaign_statistics_view(self, request, class_name=None):
        """
        Retrieve the following statistics:
        - Per World in Campaign Mode, retrieve the average score (gained per Question in the Section) and total score per Section
        - Per Section, display each Question and the number of times it was answered correctly and incorrectly
        """

        campaign_mode_stats = []  # array of worlds and their stats
        campaign_worlds = World.objects.filter(is_custom_world=False)
        for world in campaign_worlds:
            sections = Section.objects.filter(world=world)
            sections_stats = []
            for section in sections:
                # calculate total and avg points
                levels = Level.objects.filter(section=section)
                question_records = QuestionRecord.objects.filter(level__in=levels)

                # retrieve stats of students in given class, if any
                if class_name:
                    class_group = Class.objects.get(class_name=class_name)
                    students = [student_profile.student for student_profile in
                                StudentProfile.objects.filter(class_group=class_group)]
                    question_records = question_records.filter(user__in=students)

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

                    # retrieve stats of students in given class, if any
                    if class_name:
                        class_group = Class.objects.get(class_name=class_name)
                        students = [student_profile.student for student_profile in
                                    StudentProfile.objects.filter(class_group=class_group)]
                        question_record = question_record.filter(user__in=students)

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

            campaign_mode_stats.append({"world_name": world.world_name, "sections": sections_stats})

        context = {"campaign_mode_stats": campaign_mode_stats}
        if class_name:
            context["group"] = class_name
        else:
            context["group"] = "All"

        # context = {"key": "value"}
        return render(request, "main/campaign_statistics.html", context)

    # def assignment_statistics_view(self):


custom_admin_site = CustomAdminSite()

admin.site.unregister(User)
custom_admin_site.register(User, UserAdmin)

custom_admin_site.register(Token)
custom_admin_site.register(Assignment, AssignmentAdmin)
custom_admin_site.register(Question, QuestionAdmin)
custom_admin_site.register(CustomWorld, CustomWorldAdmin)
custom_admin_site.register(Section, SectionAdmin)
custom_admin_site.register(World, WorldAdmin)
custom_admin_site.register(Level, LevelAdmin)
# custom_admin_site.register(Answer, AnswerAdmin)
# admin.site.register(Assignment, AssignmentAdmin)
# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Answer, AnswerAdmin)
