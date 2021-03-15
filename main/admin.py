from django.contrib import admin
from .models import *
# Register your models here.

class AssignmentAdmin(admin.ModelAdmin):
    list_display = ('custom_world', 'class_index', 'name', 'deadline', 'date_created', 'date_modified',)
    list_filter = ('class_index',)

class AnswerAdmin(admin.TabularInline):
    model = Answer

class QuestionAdmin(admin.ModelAdmin):
    list_display = ('question', 'section', 'difficulty', 'created_by', 'date_created', 'date_modified',)
    list_filter = ('section', 'difficulty', 'created_by',)
    exclude = ['created_by', ]
    inlines = [AnswerAdmin, ]

class CustomWorldAdmin(admin.ModelAdmin):
    list_display = ('created_by', 'access_code', 'is_active',)

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(CustomWorld, CustomWorldAdmin)