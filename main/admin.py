from django.contrib import admin, messages
from django.db.models import Sum, Avg
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.template import loader
from django.urls import path
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .forms import UploadCSVForm
from .helper import calculate_world_statistics
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
            path('campaign_statistics/', self.admin_view(self.campaign_statistics_view)),
            path('assignment_statistics/', self.admin_view(self.assignment_statistics_view)),
            path('import-users/', self.admin_view(self.import_user_view))
        ]
        return custom_urls + urls

    def campaign_statistics_view(self, request):
        """
        Retrieves the following statistics:
        - Per World in Campaign Mode, retrieve the average score (gained per Question in the Section) and total score per Section
        - Per Section, display each Question and the number of times it was answered correctly and incorrectly
        """
        campaign_mode_stats = []  # array of worlds and their stats
        campaign_worlds = World.objects.filter(is_custom_world=False)
        class_name = request.GET.get("class")

        for world in campaign_worlds:
            campaign_mode_stats.append(calculate_world_statistics(world, class_name))

        context = {"campaign_mode_stats": campaign_mode_stats}
        if class_name:
            context["group"] = class_name
        else:
            context["group"] = "All"

        # create classes array for dropdown menu
        classes = ["All"]
        for class_group in Class.objects.all():
            classes.append(class_group.class_name)
        context["classes"] = classes

        return render(request, "main/campaign_statistics.html", context)

    def assignment_statistics_view(self, request):
        """
        Retrieves the following statistics:
        - For an Assignment Custom World, retrieve the average score (gained per Question in the Section), total score,
        and for each Question, the number of times it was answered correctly and incorrectly
        - If a Class name was specified, return the above statistics but only specific to that Class
        """
        access_code = request.GET.get("access_code")
        class_name = request.GET.get("class")

        # get list of assignment custom worlds and their access codes to let users choose
        # which statistics to view
        custom_worlds = [{"custom_world_name": "Choose an Assignment World", "access_code": ""}]
        teachers = User.objects.filter(is_staff=True, is_superuser=False)
        for custom_world in CustomWorld.objects.filter(created_by__in=teachers):
            custom_worlds.append({
                "custom_world_name": custom_world.world_name,
                "access_code": custom_world.access_code
            })
        context = {"custom_worlds": custom_worlds}

        # calculate stats for assignment custom world
        if access_code:
            custom_world = CustomWorld.objects.get(access_code=access_code)
            context["custom_world_stats"] = calculate_world_statistics(custom_world, class_name)

            # set current_assignment for displaying in dropdown menu
            context["current_custom_world"] = {
                "custom_world_name": custom_world.world_name,
                "access_code": access_code
            }

            # get list of classes that were assigned this assignment custom world
            classes = ["All"]
            assignments_with_this_custom_world = Assignment.objects.filter(custom_world=custom_world)
            for assignment in assignments_with_this_custom_world:
                classes.append(assignment.class_group.class_name)
            context["classes"] = classes

            # set current_class for displaying in dropdown menu
            if class_name:
                context["current_class"] = class_name
            else:
                context["current_class"] = "All"

        else:
            context["current_custom_world"] = {
                "custom_world_name": "All",
                "access_code": ""
            }

        return render(request, "main/assignment_statistics.html", context)

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
                        message += f" {len(failed_rows)} students failed to import. Please check row: <br /> {failed_rows}"

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
