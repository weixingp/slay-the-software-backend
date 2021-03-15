from django.contrib import admin
from django.db.models import Sum, Count, Avg
from django.shortcuts import render
from django.urls import path

from .models import *
from rest_framework.authtoken.models import Token

# Register your models here.

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('custom_world', 'class_index', 'name', 'deadline', 'date_created', 'date_modified',)
    list_filter = ('class_index',)

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'section', 'difficulty', 'created_by', 'date_created', 'date_modified',)
    list_filter = ('section', 'difficulty', 'created_by',)

class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'answer', 'is_correct', 'date_created', 'date_modified',)
    list_filter = ('question',)


class CustomAdminSite(admin.AdminSite):
    def get_app_list(self, request):
        app_list = super().get_app_list(request)
        app_list += [
            {
                "name": "Statistics",
                "app_label": "main",
                # "app_url": "/admin/test_view",
                "models": [
                    {
                        "name": "Campaign Mode",
                        "object_name": "TestModel",
                        "admin_url": "/admin/campaign_statistics",
                        "view_only": True,
                    }
                ],
            }
        ]
        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('campaign_statistics/', self.admin_view(self.campaign_statistic_view))
        ]
        return custom_urls + urls

    def campaign_statistic_view(self, request):
        """
        Retrieve the following statistics:
        - Per World in Campaign Mode, retrieve the average score (gained per Question in the Section) and total score per Section
        - Per Section, display each Question and the number of times it was answered correctly and incorrectly
        """
        this_teacher = request.user
        # student_points = student_records.values('user_id', 'user__first_name', 'user__last_name') \
        #     .annotate(points=Sum('points_change'))

        campaign_mode_stats = []
        campaign_worlds = World.objects.filter(is_custom_world=False)
        for world in campaign_worlds:
            sections = Section.objects.filter(world=world)
            sections_stats = []
            for section in sections:
                # calculate total and avg points
                levels = Level.objects.filter(section=section)
                question_records = QuestionRecord.objects.filter(level__in=levels)
                avg_points = question_records.aggregate(Avg('points_change'))["points_change__avg"]
                total_points = question_records.aggregate(Sum('points_change'))["points_change__sum"]

                # get stats for each question in the section
                questions_stats = []
                questions = Question.objects.filter(section=section)
                for question in questions:
                    question_record = QuestionRecord.objects.filter(question=question)
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
                    "questions_stats": questions_stats
                })

            campaign_mode_stats.append({"world_name": world.world_name, "sections": sections_stats})

        context = {"campaign_mode_stats": campaign_mode_stats}
        return render(request, "main/campaign_statistics.html", context)



custom_admin_site = CustomAdminSite()
custom_admin_site.register(User)
custom_admin_site.register(Token)
custom_admin_site.register(Assignment, AssignmentAdmin)
custom_admin_site.register(Question, QuestionAdmin)
custom_admin_site.register(Answer, AnswerAdmin)
# admin.site.register(Assignment, AssignmentAdmin)
# admin.site.register(Question, QuestionAdmin)
# admin.site.register(Answer, AnswerAdmin)
