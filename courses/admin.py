from django.contrib import admin
from django.contrib.auth import get_user_model
from rangefilter.filters import DateRangeFilter
from django.urls import reverse
from django.utils.html import format_html
from related_admin import RelatedFieldAdmin
from related_admin import getter_for_related_field
from student import models as stu_models
from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.utils.safestring import mark_safe
from . import models

# Register your models here.
USER = get_user_model()

def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper

class PersonalityTestQuestionInline(admin.TabularInline):
    model = models.PersonalityTestQuestion
    exclude = ['created_by', 'modified_by']
    fields =('personality_test', 'sno','question', 'category')
    raw_id_fields = ('personality_test', )
    extra = 3

class PTQuestionOptionInline(admin.TabularInline):
    model = models.PTQuestionOption
    exclude = ['created_by', 'modified_by']
    fields =('personality_test_question', 'sno','option')
    raw_id_fields = ('personality_test_question', )
    extra = 3

@admin.register(models.PersonalityTest)
class PersonalityTestAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['title', 'is_active', 'lang_code']
    inlines = [PersonalityTestQuestionInline,]
    list_filter = ['title']

@admin.register(models.ScholarshipTest)
class ScholarshipTestAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['title', 'is_active', 'lang_code']

@admin.register(models.ScholarshipTestQuestion)
class ScholarshipTestQuestionAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['scholarship_test','sno', 'question_type', 'question', 'lang_code']

@admin.register(models.PersonalityTestQuestion)
class PersonalityTestQuestionAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['personality_test', 'sno','question', 'category']
    raw_id_fields = ('personality_test', )
    list_filter = ['category',]
    inlines = [PTQuestionOptionInline,]

@admin.register(models.PTQuestionOption)
class PTQuestionOptionAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['personality_test_question', 'sno','option']
    raw_id_fields = ('personality_test_question', )

class ModulesInline(admin.TabularInline):
    model = models.Modules
    exclude = ['created_by', 'modified_by']
    fields = ('module_id', 'course', 'title', 'description', 'is_active', 'link_to_module', )
    extra = 0
    readonly_fields = ['module_id', 'course', 'title', 'description', 'is_active', 'link_to_module', ]

@admin.register(models.Courses)
class CoursesAdmin(admin.ModelAdmin):
    # fields=['title','description','total_modules','bg_image','duration']
    exclude = ['created_by', 'modified_by']
    list_display = ['course_id', 'title', 'description']
    list_filter = ['title', ('created_at', DateRangeFilter)]
    inlines= [ModulesInline, ]

class StepsInline(admin.TabularInline):
    model = models.Steps
    exclude = ['created_by', 'modified_by']
    fields =   ("step_sno", "title", "description", "frequency","step_completion_time", "link_to_step")
    readonly_fields = ['link_to_step' ]
    raw_id_fields = ('module',)
    extra = 3
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(models.Modules)
class ModulesAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['module_id', 'course__title','course__description', 'title',
                    'description', 'introduction_video', 'is_active']
    raw_id_fields = ('course',)
    list_filter = ['module_lang', 'course__title', ('created_at', DateRangeFilter),'is_active']
    inlines = [StepsInline,]

class ActionItemsInline(admin.TabularInline):
    model = models.ActionItems
    exclude = ['created_by', 'modified_by']
    fields =('action_sno', 'step', 'title', 'description', 'action_type', 'actionItem_completion_time', 'is_deleted', 'link_to_action_item')
    readonly_fields = ['link_to_action_item']
    raw_id_fields = ('step',)
    extra = 3
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return False


#@admin.register(models.Steps)
class StepsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['step_id','step_sno', 'title', 'description']
    raw_id_fields = ('module',)
    list_filter = ['module', ('created_at', DateRangeFilter)]
    inlines = [ActionItemsInline,]

class ActionItemLinksInline(admin.TabularInline):
    model = models.ActionItemLinks
    exclude = ['created_by', 'modified_by']
    fields =('sno', 'title','link', 'description', 'linktype', 'is_deleted', 'link_to_action_item_link')
    readonly_fields = ('link_to_action_item_link',)
    extra = 1
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return False

class ActionItemFilesInline(admin.TabularInline):
    model = models.ActionItemFiles
    exclude = ['created_by', 'modified_by']
    fields =('sno', 'title','file', 'description','file_box_heading','file_box_text','file_box_link','file_question','file_uploadbox_heading','file_uploadbox_text', 'filetype', 'is_deleted', 'link_to_action_item_file')
    readonly_fields = ('link_to_action_item_file',)
    extra = 1
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return False

class ActionItemDiaryInline(admin.TabularInline):
    model = models.ActionItemDiary
    exclude = ['created_by', 'modified_by']
    fields =('sno', 'question', 'is_deleted', 'link_to_action_item_diary')
    readonly_fields = ('link_to_action_item_diary',)
    extra = 1
    def has_add_permission(self, request, obj=None):
        return True
    def has_delete_permission(self, request, obj=None):
        return False

class ActionItemExitTicketInline(admin.TabularInline):
    model = models.ActionItemExitTicket
    exclude = ['created_by', 'modified_by']
    fields = ('sno', 'question','sub_title_question', 'type', 'is_deleted', 'link_to_action_item_exit_ticket')
    raw_id_fields = ('action_item',)
    readonly_fields = ('link_to_action_item_exit_ticket',)
    extra = 1
    def has_add_permission(self, request, obj=None) -> bool:
        return True
    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(models.WebinarQuestionnaire)
class WebinarQuestionnaireAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['title', 'test_type', 'is_active', 'lang_code']
    list_filter = ['is_active', 'lang_code', 'test_type']

@admin.register(models.WebinarQuestion)
class WebinarQuestionAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['question', 'webinar_test']
    list_filter = ['webinar_test']


class ActionItemTypeTableInline(admin.TabularInline):
    model = models.ActionItemTypeTable
    exclude = ['created_by', 'modified_by']
    fields = ('sno', 'title', 'file_link', 'description', 'questions', 'is_deleted', 'link_to_action_item_type_table')
    # raw_id_fields = ('action_item',)
    readonly_fields = ('link_to_action_item_type_table',)
    extra = 1
    def has_add_permission(self, request, obj=None) -> bool:
        return True
    def has_delete_permission(self, request, obj=None) -> bool:
        return False

class ActionItemTypeTableStep8Inline(admin.TabularInline):
    model = models.ActionItemTypeTableStep8
    exclude = ['created_by', 'modified_by']
    fields = ('sno', 'title', 'description', 'criteria_question_head','criteria_question_text', 'is_deleted', 'link_to_action_item_type_table_step8')
    # raw_id_fields = ('action_item',)
    readonly_fields = ('link_to_action_item_type_table_step8',)
    extra = 5
    def has_add_permission(self, request, obj=None) -> bool:
        return True
    def has_delete_permission(self, request, obj=None) -> bool:
        return False

class ActionItemGoogleFormInline(admin.TabularInline):
    model = models.ActionItemGoogleForm
    exclude = ['created_by', 'modified_by']
    fields = ('sno', 'title', 'description', 'file_link','question', 'type', 'is_deleted', 'link_to_action_item_google_form')
    # raw_id_fields = ('action_item',)
    readonly_fields = ('link_to_action_item_google_form',)
    extra = 3
    def has_add_permission(self, request, obj=None) -> bool:
        return True
    def has_delete_permission(self, request, obj=None) -> bool:
        return False
    
class ActionItemFrameworkInline(admin.TabularInline):
    model = models.ActionItemFramework
    exclude = ['created_by', 'modified_by']
    fields = ('sno', 'title', 'description', 'questions', 'is_deleted', 'link_to_action_item_framework')
    readonly_fields = ('link_to_action_item_framework',)
    extra = 1
    def has_add_permission(self, request, obj=None) -> bool:
        return True
    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(models.ActionItems)
class ActionItemsAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_id','action_sno', 'step__title', 'title', 'description', 'action_type', 'is_deleted']
    raw_id_fields = ('step',)
    list_filter = ['action_type',('step__title', custom_titled_filter('Steps')), ('step__module__title', custom_titled_filter('Modules'))]
    step__title = getter_for_related_field('step__title', short_description='Step Title')
    inlines = [ActionItemLinksInline,ActionItemDiaryInline,ActionItemFilesInline, ActionItemExitTicketInline, ActionItemTypeTableInline, ActionItemTypeTableStep8Inline, ActionItemGoogleFormInline, ActionItemFrameworkInline]
    
    # def link_to_action_item1(self,obj):
    #     link=reverse("admin:courses_actionitems_change", args=[obj.action_id]) #model name has to be lowercase
    #     return format_html(f'<a href="{link}" target="_blank">{obj.title}</a>')

@admin.register(models.ActionItemConnectWithOtherActionItem)
class ActionItemConnectWithOtherActionItemAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['primary_action_item', 'secondary_action_item', 'ai_relation_type', 'is_deleted']
    raw_id_fields = ('primary_action_item', 'secondary_action_item',)
    list_filter = ['ai_relation_type']
    ai_relation_type = getter_for_related_field('ai_relation_type', short_description='Action Item Relation Type')

@admin.register(models.ActionItemTypeTable)
class AdminActionItemTypeTable(RelatedFieldAdmin):
    exclude = ["created_by", "modified_by"]
    list_display = ['action_item', 'sno', 'title', 'file_link', 'description', 'questions', 'is_deleted']
    raw_id_fields = ('action_item',)

@admin.register(models.ActionItemGoogleFormOption)
class AdminActionItemGoogleFormOption(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_item_google_form', 'sno', 'option', 'option_type', 'is_deleted']
    raw_id_fields = ('action_item_google_form',)

class ActionItemGoogleFormOptionInline(admin.TabularInline):
    model = models.ActionItemGoogleFormOption
    exclude = ['created_by', 'modified_by']
    fields = ('sno', 'option', 'option_type', 'is_deleted', 'link_to_action_item_google_form_option')
    readonly_fields = ('link_to_action_item_google_form_option',)
    extra = 2
    def has_add_permission(self, request, obj=None) -> bool:
        return True
    def has_delete_permission(self, request, obj=None) -> bool:
        return True
    
@admin.register(models.ActionItemGoogleForm)
class AdminActionItemGoogleForm(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_item', 'sno', 'title', 'type', 'file_link', 'description', 'question', 'is_deleted']
    raw_id_fields = ('action_item',)
    inlines = [ActionItemGoogleFormOptionInline,]

@admin.register(models.ActionItemFramework)
class AdminActionItemFramework(RelatedFieldAdmin):
    exclude = ["created_by", "modified_by"]
    list_display = ['action_item', 'sno', 'title', 'description', 'questions', 'is_deleted']
    raw_id_fields = ('action_item',)

@admin.register(models.ActionItemTypeTableStep8)
class AdminActionItemTypeTableStep8(RelatedFieldAdmin):
    exclude = ["created_by", "modified_by"]
    list_display = ['action_item', 'sno', 'title', 'description', 'criteria_question_head','criteria_question_text', 'is_deleted']
    raw_id_fields = ('action_item',)

@admin.register(models.ActionDataTypes)
class ActionDataTypesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'datatype']
    # list_filter = ['datatype']

@admin.register(models.ActionFileTypes)
class ActionFileTypesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'filetype']
    # list_filter = ['filetype']


@admin.register(models.ActionLinkTypes)
class ActionLinkTypesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'linktype']
    # list_filter = ['linktype']


@admin.register(models.ActionItemLinks)
class ActionItemLinksAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item', 'title', 'link', 'is_deleted']
    raw_id_fields = ('action_item',)
    list_filter = ['linktype']
    search_fields = ['title']


@admin.register(models.ActionItemFiles)
class ActionItemFilesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item', 'title', 'file','file_box_heading','file_box_text','file_question','file_uploadbox_heading','file_uploadbox_text', 'is_deleted']
    raw_id_fields = ('action_item',)
    list_filter = ['filetype']
    search_fields = ['title']


@admin.register(models.ActionItemDiary)
class ActionItemDiaryAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item', 'question', 'is_linked_with_ai_comment', 'is_deleted']
    raw_id_fields = ('action_item',)
    list_filter = ['action_item','is_linked_with_ai_comment']
    search_fields = ['question']

@admin.register(models.ActionItemExitTicket)
class ActionItemExitTicketAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item', 'question', 'sub_title_question', 'type', 'is_deleted']
    raw_id_fields = ('action_item',)
    list_filter = ['type','action_item']
    search_fields = ['question']

@admin.register(models.ActionItemExitTicketOptions)
class ActionItemExitTicketOptionsAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item_exit_ticket__question', 'option', 'is_deleted']
    raw_id_fields = ('action_item_exit_ticket',)
    search_fields = ['option']

@admin.register(models.OurPlans)
class OurPlansAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['plan_name','title','cost','upgrade_cost','weekly_cost','pcto_hour_limit']
    list_filter = ['plan_lang']
    search_fields = ['plan_name', 'title', 'sub_title', 'description']


class StepStatusInline(admin.TabularInline):
    model = models.step_status
    exclude = ['created_by', 'modified_by']
    fields =('cohort', 'step', 'starting_date','link_to_step_status')
    raw_id_fields = ('cohort', 'step')
    readonly_fields = ['link_to_step_status' ]
    extra = 3

@admin.register(models.Cohort)
class CohortAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['cohort_id', 'module', 'cohort_name',
                    'starting_date', 'price', 'duration',"cohort_type"]
    raw_id_fields = ('module',)
    list_filter = ['cohort_lang',"cohort_type", 'is_active', 'module', ('starting_date', DateRangeFilter)]
    search_fields = ['cohort_name',]
    inlines = [StepStatusInline,]


@admin.register(models.step_status)
class StepStatusAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['cohort', 'step', 'starting_date']
    raw_id_fields = ('cohort', 'step')
    list_filter = ['cohort', 'step', ('starting_date', DateRangeFilter)]
    search_fields = ['cohort_name',]
    


@admin.register(models.Blog_post)
class Blog_postAdmin(admin.ModelAdmin):
    list_display = ('title', 'blog_link', 'author', 'publish_date', 'status')
    exclude = ['created_by', 'modified_by', 'slug', 'body']
    #list_filter = ('status', 'created_at', 'publish_date', 'author')
    #search_fields = ('title', 'body')
    #prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'publish_date'
    ordering = ('status', 'publish_date')
    list_filter = ['status', 'module_lang', ('publish_date', DateRangeFilter)]
    search_fields = ['title', 'slug', 'body']


@admin.register(models.Webinars)
class WebinarsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by', 'description']
    list_display = ('title', 'author', 'webinar_start_date', 'reservation_start_date', 'status','maximum_seats','allocated_seats','attendance_code', 'hubspot_properties')
    raw_id_fields = ('author',)
    list_filter = ['status', 'module_lang', ('webinar_start_date', DateRangeFilter)]
    search_fields = ['title', 'description']


@admin.register(models.Notification_type)
class Notification_typeAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('notification_type',)
    list_filter = ['notification_type']
    search_fields = ['description']


@admin.register(models.Notification)
class NotificationAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('cohort', 'student', 'title', 'notification_type', 'created_at')
    raw_id_fields = ('cohort', 'student')
    list_filter = ['notification_type']
    search_fields = ['title']


@admin.register(models.MyGroups)
class MyGroupsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('cohort', 'group_title', 'group_link')
    raw_id_fields = ('cohort',)
    list_filter = ['group_type']
    search_fields = ['group_title']


@admin.register(models.MyVideos)
class MyVideosAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('video_title', 'video_link')
    list_filter = ['module_lang']
    search_fields = ['video_title', 'video_description']

@admin.register(models.WelcomeVideo)
class WelcomeVideoAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('video_title', 'video_link')
    list_filter = ['module_lang']
    search_fields = ['video_title', 'video_description']

@admin.register(models.MyPdfs)
class MyPdfsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('pdf_title', 'pdf_file')
    list_filter = ['module_lang']

@admin.register(models.MyResources)
class MyResourcesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('resource_title', 'resource_link')
    list_filter = ['module_lang']
    search_fields = ['resource_title', 'resource_description']

@admin.register(models.MyBlogVideos)
class MyBlogVideosAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('title', 'link','publish_date','type','module_lang', 'is_for_fast_track', 'sno', 'duration')
    list_filter = ['module_lang', 'status', 'type', ('publish_date', DateRangeFilter), 'is_for_fast_track']
    search_fields = ['title', 'description']

admin.site.register(models.Steps,StepsAdmin)

@admin.register(models.MeetupCommunity)
class MeetupCommunityAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('title', 'meet_link', 'meet_day', 'meet_time', 'meet_tutor_name','is_Active')

@admin.register(models.Meetup)
class MeetupAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('cohort','step_status','title', 'meet_link', 'meet_date_time', 'meet_tutor_name','is_Active')
    raw_id_fields = ('cohort', 'step_status')
    

@admin.register(models.EmailTemplate)
class AdminEmailTemplates(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('template_name', 'template_file')
    search_fields = ['template_name']


@admin.register(models.EmailForwadingDetails)
class AdminEmailForwordingDetails(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('id' ,'excel_file', 'emailtemplate_id')


@admin.register(models.PushNotificationTopics)
class AdminPushNotificationTopics(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('id' ,'topic_name')

@admin.register(models.PushNotificationRecords)
class AdminPushNotificationRecords(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    raw_id_fields = ('topic', )
    list_display = ('id' ,'topic__topic_name','title', 'body','response_msg_id')

@admin.register(models.CohortPushNotificationRecords)
class AdminCohortPushNotificationRecords(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('id' ,'topic','title', 'body','response_msg_id')


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'

    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return mark_safe(link)
    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"

@admin.register(models.TestCohortID)
class AdminTestCohortID(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('cohort',)
    raw_id_fields = ('cohort',)

@admin.register(models.JobPosting)
class JobPostingAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['title', 'company_name', 'company_logo','location','job_portal_link','is_active', 'company_to_display_specific_jobs']
    list_filter = ['is_active','company_name','location', 'company_to_display_specific_jobs']
    raw_id_fields = ('company_to_display_specific_jobs',)

