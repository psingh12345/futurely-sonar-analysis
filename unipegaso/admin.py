from django.contrib import admin
from .models import *


class UnipagesoStudentPTMapperInline(admin.TabularInline):
    model = UnipagesoStudentPTMapper
    fields = ['unipegaso_test', 'rising_test_result', 'is_completed', 'link_to_unipegaso_student_pt_mapper']
    raw_id_fields = ('unipegaso_test', 'student_detail',)
    readonly_fields = ('unipegaso_test', 'rising_test_result', 'is_completed', 'link_to_unipegaso_student_pt_mapper')
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class UnipagesoStudentNextQuestionTrackerInline(admin.TabularInline):
    model = UnipagesoStudentNextQuestionTracker
    fields = ['unipegaso_ai_next_question', 'answer', 'link_to_tracker']
    raw_id_fields = ('student_detail', 'unipegaso_ai_next_question', )
    readonly_fields = ('unipegaso_ai_next_question', 'answer', 'link_to_tracker')
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False



@admin.register(StudentDetail)
class StudentDetailAdmin(admin.ModelAdmin):
    fields = ['email', 'first_name', 'last_name', 'phone_number', 'college', 'year_of_enrollment',
            'session_id', 'assessment_status', 'are_you_taking_this_test_at_a_contracted_center', 'test_at_a_contracted_center_other', 'certificate_link','clarity_token']
    list_display = ('email', 'first_name', 'last_name', 'phone_number', 'college', 'year_of_enrollment', 
                    'session_id', 'assessment_status', 'are_you_taking_this_test_at_a_contracted_center', 'test_at_a_contracted_center_other', 'certificate_link','clarity_token')
    search_fields = ["email", "first_name", 'last_name','clarity_token']
    inlines = [UnipagesoStudentPTMapperInline, UnipagesoStudentNextQuestionTrackerInline, ]

class UniPegasoActionItemsPTQuestionInline(admin.TabularInline):
    model = UniPegasoActionItemsPTQuestion
    fields = ['question', 'question_type', 'question_category', 'link_to_pt_question']
    raw_id_fields = ('unipegaso_test',)
    readonly_fields = ['link_to_pt_question']
    extra = 3
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return True

class UnipegasoActionItemsNextQuestionInline(admin.TabularInline):
    model = UnipegasoActionItemsNextQuestion
    fields = ['sno', 'question', 'question_type', 'link_to_next_question']
    raw_id_fields = ('unipegaso_test',)
    readonly_fields = ['link_to_next_question']
    extra = 3
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(UnipegasoTest)
class UnipegasoTestAdmin(admin.ModelAdmin):
    fields = ['action_item_name', 'type']
    list_display = ('action_item_name', 'type',)
    inlines = [UniPegasoActionItemsPTQuestionInline, UnipegasoActionItemsNextQuestionInline]

class UnipegasoStudentPTAnswerInline(admin.TabularInline):
    model = UnipegasoStudentPTAnswer
    fields = ['unipegaso_student_mapper', 'unipegaso_question', 'answer', 'is_completed', 'link_to_link_to_answer']
    raw_id_fields = ('unipegaso_student_mapper', 'unipegaso_question',)
    readonly_fields = ['unipegaso_question', 'answer', 'is_completed', 'link_to_link_to_answer']
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(UnipagesoStudentPTMapper)
class UnipagesoStudentPTMapperAdmin(admin.ModelAdmin):
    fields = ['unipegaso_test', 'student_detail', 'rising_test_result', 'is_completed']
    list_display = ('unipegaso_test', 'student_detail','rising_test_result', 'is_completed')
    raw_id_fields = ('unipegaso_test', 'student_detail', )
    inlines = [UnipegasoStudentPTAnswerInline]


class UniPegasoActionItemPTOptionInline(admin.TabularInline):
    model = UniPegasoActionItemPTOption
    fields = ['unipegaso_question', 'option']
    raw_id_fields = ('unipegaso_question',)
    extra = 2
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

@admin.register(UniPegasoActionItemsPTQuestion)
class UniPegasoActionItemsPTQuestionAdmin(admin.ModelAdmin):
    fields = ['question', 'question_type', 'question_category', 'unipegaso_test']
    list_display = ('unipegaso_test', 'question', 'question_type', 'question_category')
    search_fields = ['question', 'question_type']
    raw_id_fields = ('unipegaso_test',)
    inlines = [UniPegasoActionItemPTOptionInline,]

class UnipegasoActionItemsNextQuestionOptionInline(admin.TabularInline):
    model = UnipegasoActionItemsNextQuestionOption
    fields = ['unipegaso_next_question', 'option']
    raw_id_fields = ('unipegaso_next_question',)
    extra = 2
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

class UnipegasoActionItemsNextQuestionVideosInline(admin.TabularInline):
    model = UnipegasoActionItemsNextQuestionVideo
    fields = ['video_link', 'unipegaso_next_question']
    raw_id_fields = ('unipegaso_next_question',)
    extra = 2
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
@admin.register(UnipegasoActionItemsNextQuestionVideo)
class UnipegasoActionItemsNextQuestionVideosAdmin(admin.ModelAdmin):
    fields = ['unipegaso_next_question', 'video_link']
    list_display = ('unipegaso_next_question', 'video_link')
    raw_id_fields = ('unipegaso_next_question',)

class UnipegasoVideoOptionLinkInline(admin.TabularInline):
    model = UnipegasoVideoOptionLink
    fields = ['unipegaso_option', 'link']
    raw_id_fields = ('unipegaso_option',)
    extra = 1
    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True
    
@admin.register(UnipegasoActionItemsNextQuestionOption)
class UnipegasoActionItemsNextQuestionOptionAdmin(admin.ModelAdmin):
    fields = ['unipegaso_next_question', 'option']
    list_display = ('unipegaso_next_question', 'option')
    raw_id_fields = ('unipegaso_next_question',)
    inlines = [UnipegasoVideoOptionLinkInline]

@admin.register(UnipegasoActionItemsNextQuestion)
class UniPegasoQuestionAdmin(admin.ModelAdmin):
    fields = ['sno','unipegaso_test', 'question', 'question_type']
    list_display = ('sno', 'unipegaso_test', 'question', 'question_type')
    search_fields = ['unipegaso_test', 'question', 'question_type']
    raw_id_fields = ('unipegaso_test',)
    inlines = [UnipegasoActionItemsNextQuestionOptionInline, UnipegasoActionItemsNextQuestionVideosInline,]


@admin.register(UniPegasoActionItemPTOption)
class UniPegasoQuestionOptionAdmin(admin.ModelAdmin):
    raw_id_fields = ['unipegaso_question',]
    fields = ['unipegaso_question', 'option']
    list_display = ('unipegaso_question', 'option',)
    search_fields = ['option', 'unipegaso_question__question']

@admin.register(UnipagesoStudentNextQuestionTracker)
class UnipagesoStudentNextQuestionTrackerAdmin(admin.ModelAdmin):
    raw_id_fields = ['unipegaso_ai_next_question']
    fields = ['unipegaso_ai_next_question', 'answer']
    list_display = ('unipegaso_ai_next_question', 'answer',)

@admin.register(UnipegasoStudentPTAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    raw_id_fields = ['unipegaso_student_mapper', 'unipegaso_question']
    fields = ['unipegaso_student_mapper', 'unipegaso_question', 'answer', 'is_completed']
    list_display = ('unipegaso_student_mapper', 'unipegaso_question', 'answer', 'is_completed')
    search_fields = ['unipegaso_question__question',]

@admin.register(ApprovedCentreOption)
class ApprovedCentreOptionAdmin(admin.ModelAdmin):
    fields = ['option', 'option_type']
    list_display = ('pk', 'option', 'option_type')
    search_fields = ['option', 'option_type']
    list_filter = ('option_type',)

@admin.register(UnipegasoVideoOptionLink)
class UnipegasoVideoOptionLinkAdmin(admin.ModelAdmin):
    fields = ['unipegaso_option', 'link',]
    # search_fields = ['option',]