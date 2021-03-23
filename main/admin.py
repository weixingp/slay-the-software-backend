from django.contrib import admin, messages
from django.db.models import Sum, Avg
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import path
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UploadCSVForm
from .models import *
from .views import CampaignStatisticsView, AssignmentStatisticsView
from rest_framework.authtoken.models import Token


# Register your models here.
from .utils import import_users


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
            },
            {
                "name": "Tools",
                "app_label": "main",
                "models": [
                    {
                        "name": "Import users",
                        "object_name": None,
                        "admin_url": "/admin/import-users/",
                        "view_only": True,
                    },
                ]
            }
        ]
        return app_list

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('campaign_statistics/', CampaignStatisticsView.as_view()),
            path('assignment_statistics/', AssignmentStatisticsView.as_view()),
            path('import-users/', self.admin_view(self.import_user_view))
        ]
        return custom_urls + urls

    def import_user_view(self, request):
        """
        Import student from CSV page for teachers and admins
        """
        template = loader.get_template('admin/import-users.html')

        if request.method == "GET":
            # Viewing the page
            class_groups = Class.objects.all()
            context = dict(
                # Include common variables for rendering the admin template.
                self.each_context(request),
                # Anything else you want in the context...
                title="Import users",
                proccessed=False,
                class_groups=class_groups,
            )

            response = HttpResponse(template.render(context, request))
            return response

        elif request.method == "POST":
            # Process upload
            form = UploadCSVForm(data=request.POST, files=request.FILES)
            if form.is_valid():
                class_group = form.cleaned_data['class_group']
                csv = request.FILES['csv_file']
                try:
                    total, failed_rows = import_users(csv, class_group)
                    message = f"{total - len(failed_rows)} students imported successfully."
                    if failed_rows:
                        message += f" {2} students failed to import. Please check row: <br /> {failed_rows}"

                    message += "<br /><br /> <a href='.'>Import more students</a>"
                except Exception as ex:
                    messages.add_message(request, messages.ERROR, f'Unable to process CSV file. Error: {repr(ex)}')
                    message = "Something went wrong."
            else:
                message = "Invalid class group or CSV file, please <a href='.'>try again.</a>"

            context = dict(
                # Include common variables for rendering the admin template.
                self.each_context(request),
                # Anything else you want in the context...
                title="Import users",
                processed=True,
                message=message,
            )

            response = HttpResponse(template.render(context, request))
            return response

        else:
            return redirect("/admin")

    def import_user_action_view(self, request):
        """
        Json action view to accept csv file.
        """


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
