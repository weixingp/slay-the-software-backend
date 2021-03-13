from django.contrib import admin
from .models import *
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

admin.site.register(Assignment, AssignmentAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Answer, AnswerAdmin)
