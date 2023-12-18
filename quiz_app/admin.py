from django.contrib import admin
from .import models
from django.urls import reverse
from django.utils.html import format_html

class QuizQuestionInline(admin.TabularInline):
    model = models.QuizQuestion
    fields = ['sno', 'quiz', 'question', 'question_type', 'is_active', 'quiz_question_link']
    raw_id_fields = ['quiz']
    readonly_fields = ['quiz', 'quiz_question_link']

    def quiz_question_link(self, instance):
        link=reverse("admin:quiz_app_quizquestion_change", args=[instance.id])
        return format_html(f'<a href="{link}" target="_blank">Click Me!</a>')

@admin.register(models.Quiz)
class QuizAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'modified_at')
    list_display = ['title', 'description', 'duration', 'quiz_banner', 'is_active', 'correct_answer_point', 'deduction_answer_point']
    # fields = ['title', 'description', 'duration', 'quiz_banner', 'is_active']
    search_fields = ['title', 'description']
    inlines = [QuizQuestionInline,]

class QuizQuestionOptionInline(admin.TabularInline):
    model = models.QuizQuestionOption
    fields = ['question', 'option','is_correct', 'option_link']
    readonly_fields = ['option_link',]
    raw_id_fields = ['question']

    def option_link(self, instance):
        link=reverse("admin:quiz_app_quizquestionoption_change", args=[instance.id])
        return format_html(f'<a href="{link}" target="_blank">Click Me!</a>')

@admin.register(models.QuizQuestion)
class QuizzQuestionAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'modified_at')
    list_display = ['sno', 'quiz', 'question', 'question_type', 'is_active']
    fields = ['sno', 'quiz', 'question', 'question_type', 'is_active']
    raw_id_fields = ['quiz']
    search_fields = ['question',]
    inlines = [QuizQuestionOptionInline, ]

@admin.register(models.QuizQuestionOption)
class QuizzQuestionOptionsAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'modified_at')
    list_display = ['question', 'option','is_correct']
    fields = ['question', 'option','is_correct']
    raw_id_fields = ['question']

class QuizStudentAnswerInline(admin.TabularInline):
    model = models.QuizStudentAnswer
    fields = ['stu_mapper', 'question','answer']
    raw_id_fields = ['stu_mapper', 'question',]

@admin.register(models.QuizStudentMapper)
class QuizzStudentMapperAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'modified_at')
    list_display = ['student', 'quiz','is_completed', 'score']
    # fields = ['student', 'quiz','is_completed']
    raw_id_fields = ['student','quiz']
    inlines = [QuizStudentAnswerInline,]

@admin.register(models.QuizStudentAnswer)
class QuizzStudentAnswerAdmin(admin.ModelAdmin):
    exclude = ('created_at', 'modified_at')
    list_display = ['stu_mapper', 'question','answer']
    fields = ['stu_mapper', 'question','answer']
    raw_id_fields = ['stu_mapper', 'question']
