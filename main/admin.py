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
        this_teacher = request.user
        student_records = QuestionRecord.objects.all()
        # student_points = student_records.values('user_id', 'user__first_name', 'user__last_name') \
        #     .annotate(points=Sum('points_change'))
        campaign_worlds = World.objects.filter(is_custom_world=False)
        for world in campaign_worlds:
            sections = Section.objects.filter(world=world)
            for section in sections:
                levels = Level.objects.get(section=section)
                for level in levels:
                    question_records = Question.objects.filter(level=level)
                    avg_points = question_records.aggregate(Avg('points_change'))["points_change__avg"]




        context = {"student_points": "placeholder"}
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
