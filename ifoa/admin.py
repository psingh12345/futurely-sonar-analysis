from django.contrib import admin
from .models import *

class IFOAStudentPTMapperInline(admin.TabularInline):
    model = IFOAStudentPTMapper
    fields = ['ifoa_student_detail', 'ifoa_test', 'test_result', 'is_completed',]
    raw_id_fields = ['ifoa_student_detail', 'ifoa_test',]
    readonly_fields = ['ifoa_student_detail', 'ifoa_test', 'test_result', 'is_completed',]
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

class IFOAStudentQuestionTrackerInline(admin.TabularInline):
    model = IFOAStudentQuestionTracker
    fields = ['ifoa_student_detail', 'ifoa_question', 'answer']
    raw_id_fields = ['ifoa_student_detail', 'ifoa_question',]
    readonly_fields = ['ifoa_student_detail', 'ifoa_question', 'answer']
    extra = 0
    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(IFOAStudentDetail)
class IFOAStudentDetailAdmin(admin.ModelAdmin):
    list_display = ["id", 
                    "first_name", 
                    "last_name", 
                    "email", 
                    "phone_number", 
                    "gender", 
                    'date_of_birth',
                    'birth_place',
                    'tax_id_code',
                    'tax_id_code',
                    'how_did_you_know_us',
                    'assessment_status',
                    'session_id',
                    'certificate_link',]
    
    search_fields = ['first_name', 'last_name', 'email', 'phone_number', 'tax_id_code']
    inlines = [IFOAStudentPTMapperInline, IFOAStudentQuestionTrackerInline]

class IFOAPTQuestionInlines(admin.TabularInline):
    model = IFOAPTQuestion
    fields = ['ifoa_test', 'question', 'question_type', 'question_category']
    raw_id_fields = ['ifoa_test',]
    extra = 2

class IFOAQuestionInline(admin.TabularInline):
    model = IFOAQuestion
    fields = ['sno', 'ifoa_test', 'question', 'question_type']
    raw_id_fields = ['ifoa_test',]
    # search_fields = ['question', 'question_type']
    extra = 2

@admin.register(IFOATest)
class IFOATestAdmin(admin.ModelAdmin):
    list_display = ["id", 
                    "test_title", 
                    "type", ]
    search_fields = ['type', 'test_title']
    inlines = [IFOAPTQuestionInlines, IFOAQuestionInline]
    
class IFOAPTQuestionMCQOptionInline(admin.TabularInline):
    model = IFOAPTQuestionMCQOption
    fields = ['ifoa_question', 'option']
    raw_id_fields = ['ifoa_question',]
    extra = 2

@admin.register(IFOAPTQuestionMCQOption)
class IFOAPTQuestionMCQOptionAdmin(admin.ModelAdmin):
    list_display = ["id", "ifoa_question", "option",]
    raw_id_fields = ['ifoa_question',]
    search_fields = ['option',]

@admin.register(IFOAPTQuestion)
class IFOAPTQuestionAdmin(admin.ModelAdmin):
    list_display = ["id", 
                    "ifoa_test", 
                    "question",
                    'question_type',
                    'question_category',
                    ]
    list_filter = ['question_type', 'question_category']
    search_fields = ['question',]
    inlines = [IFOAPTQuestionMCQOptionInline,]

class IFOAQuestionMCQOptionInline(admin.TabularInline):
    model = IFOAQuestionMCQOption
    fields = ['ifoa_question', 'option']
    raw_id_fields = ['ifoa_question',]
    # readonly_fields = ('option_link',)
    extra = 2
    # def option_link(self, instance):
    #     if instance.pk:
    #         return f'<a href="{instance.get_absolute_url()}">{instance}</a>'
    #     return "-"
    # option_link.allow_tags = True  # Allow the HTML tags to render the link properly
    # option_link.short_description = 'Option Model Link'

class IFOAQuestionLinkInline(admin.TabularInline):
    model = IFOAQuestionLink
    fields = ['ifoa_question', 'link']
    raw_id_fields = ['ifoa_question',]
    extra = 2

@admin.register(IFOAQuestion)
class IFOAQuestionAdmin(admin.ModelAdmin):
    list_display = [
                    "id",
                    "sno", 
                    "ifoa_test", 
                    "question",
                    'question_type',
                    ]
    raw_id_fields = ['ifoa_test',]
    search_fields = ['question',]
    list_filter = ['question_type',]
    inlines = [IFOAQuestionMCQOptionInline, IFOAQuestionLinkInline] 

class IFOAQuestionOptionLinkInline(admin.TabularInline):
    model = IFOAQuestionOptionLink
    fields = ['ifoa_question_option', 'video_link']
    raw_id_fields = ['ifoa_question_option',]
    extra = 2

class IFOAQuestionMCQOptionLinkedQuestionInline(admin.TabularInline):
    model = IFOAQuestionMCQOptionLinkedQuestion
    fields = ['ifoa_question_mcq_option', 'ifoa_question']
    raw_id_fields = ['ifoa_question_mcq_option', 'ifoa_question']
    extra = 0

@admin.register(IFOAQuestionMCQOption)
class IFOAQuestionMCQOptionAdmin(admin.ModelAdmin):
    list_display = ["id", 
                    "ifoa_question", 
                    "option",
                    ]
    raw_id_fields = ['ifoa_question',]
    search_fields = ['option',]
    inlines = [IFOAQuestionOptionLinkInline, IFOAQuestionMCQOptionLinkedQuestionInline]

@admin.register(IFOAQuestionMCQOptionLinkedQuestion)
class IFOAQuestionMCQOptionLinkedQuestionAdmin(admin.ModelAdmin):
    list_display = ["id", "ifoa_question_mcq_option", "ifoa_question",]
    raw_id_fields = ['ifoa_question_mcq_option', 'ifoa_question',]

@admin.register(IFOAQuestionOptionLink)
class IFOAQuestionOptionLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "ifoa_question_option", "video_link",]
    raw_id_fields = ['ifoa_question_option',]
    search_fields = ['video_link',]

@admin.register(IFOAQuestionLink)
class IFOAQuestionLinkAdmin(admin.ModelAdmin):
    list_display = ["id", "ifoa_question", "link",]
    raw_id_fields = ['ifoa_question',]
    search_fields = ['link',]

@admin.register(IFOAStudentPTMapper)
class IFOAStudentPTMapperAdmin(admin.ModelAdmin):
    list_display = ["id", 
                    "ifoa_student_detail", 
                    "ifoa_test",
                    'test_result',
                    'is_completed',
                    ]
    raw_id_fields = ['ifoa_student_detail', 'ifoa_test']
    list_filter = ['test_result', 'is_completed']
    search_fields = ['ifoa_student_detail', 'ifoa_test']

@admin.register(IFOAStudentQuestionTracker)
class IFOAStudentNextQuestionTrackerAdmin(admin.ModelAdmin):
    list_display = ["id", "ifoa_student_detail", "ifoa_question",'answer',]
    raw_id_fields = ['ifoa_student_detail', 'ifoa_question']
    search_fields = ['ifoa_student_detail', 'ifoa_question']

@admin.register(IFOAStudentPTAnswer)
class IFOAStudentPTAnswerAdmin(admin.ModelAdmin):
    list_display = ["id", 
                    "ifoa_student_mapper", 
                    "ifoa_question",
                    'answer',
                    'is_completed',
                    ]
    raw_id_fields = ['ifoa_student_mapper', 'ifoa_question']
    search_fields = ['ifoa_student_mapper', 'ifoa_question']