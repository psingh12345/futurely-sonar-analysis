from django.contrib import admin
from django.contrib.auth import get_user_model
from rangefilter.filters import DateRangeFilter
from . import models
from courses import models as course_models
from related_admin import RelatedFieldAdmin
from related_admin import getter_for_related_field
from userauth import models as AuthModels
# Register your models here.


def custom_titled_filter(title):
    class Wrapper(admin.FieldListFilter):
        def __new__(cls, *args, **kwargs):
            instance = admin.FieldListFilter.create(*args, **kwargs)
            instance.title = title
            return instance
    return Wrapper


@admin.register(models.StudentWebinarMapper)
class StudentWebinarMapperAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student__username', 'webinar_questionnaire',
                    'webinar', 'is_completed', 'lang_code']


@admin.register(models.StudentWebinarAnswer)
class StudentWebinarAnswerAdmin(RelatedFieldAdmin):
    exclude = ["created_by", "modified_by"]
    list_display = ["stu_webinar_mapper",
                    "webinar_question", "webinar_answer", "is_completed"]


@admin.register(models.StudentActionItemDiaryComment)
class StudentActionItemDiaryCommentAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['person__username',
                    'student_actions_item_diary_id', 'is_active', 'comment']
    search_fields = ["person__username"]
    raw_id_fields = ('student_actions_item_diary_id', 'person')


@admin.register(models.StudentActionItemDiaryAIComment)
class StudentActionItemDiaryAICommentAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student_actions_item_diary_id',
                    'ai_comment', 'ai_comment_status']
    raw_id_fields = ('student_actions_item_diary_id',)


@admin.register(models.StudentsPlanMapper)
class StudentsPlanMapperAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'student', 'student__username',
                    'plans__title', "is_trial_active", "trial_type"]
    raw_id_fields = ('student',)
    list_filter = ['plans', 'plan_lang', "is_trial_active", "trial_type"]
    search_fields = ['student__username']


@admin.register(models.StudentScholarshipTestMapper)
class StudentScholarshipTestMapperAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['scholarship_test', 'student__username',
                    'last_answered', 'is_applied', 'lang_code']
    list_filter = ['is_applied', 'lang_code']


@admin.register(models.StudentScholarShipTest)
class StudentScholarShipTestAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['stu_scholarshipTest_mapper__scholarship_test', 'stu_scholarshipTest_mapper__student__username',
                    'scholarshipTest_question__question', 'scholarshipTest_answer', 'is_completed']


class CohortStepTrackerInline(admin.TabularInline):
    model = models.CohortStepTracker
    exclude = ['created_by', 'modified_by']
    fields = ('step_status_id', 'stu_cohort_map',
              'is_completed', 'link_to_cohortstep_tracker')
    readonly_fields = ['step_status_id', 'stu_cohort_map',
                       'is_completed', 'link_to_cohortstep_tracker']
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.StudentCohortMapper)
class StudentCohortMapperAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['stu_cohort_map_id', 'student','student__username', 'cohort']
    raw_id_fields = ('cohort', 'student','student_plan')
    list_filter = ['stu_cohort_lang','cohort']
    search_fields = ['student__username']
    inlines = [CohortStepTrackerInline]


class StudentActionItemTrackerInline(admin.TabularInline):
    model = models.StudentActionItemTracker
    exclude = ['created_by', 'modified_by']
    fields = ('Action_item_track_id', 'step_tracker', 'ActionItem',
              'is_completed', 'link_to_studentactionitemtracker', )
    readonly_fields = ['Action_item_track_id', 'step_tracker',
                       'ActionItem', 'is_completed', 'link_to_studentactionitemtracker',]
    raw_id_fields = ('step_tracker', 'ActionItem')
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class CohortStepTrackerDetailsInline(admin.TabularInline):
    model = models.CohortStepTrackerDetails
    exclude = ['created_by', 'modified_by']
    fields = ('cohort_step_tracker', 'last_commented_date_time',
              'step_completion', 'total_comments')
    raw_id_fields = ('cohort_step_tracker',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return True

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(models.CohortStepTracker)
class CohortStepTrackerAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['step_track_id', 'stu_cohort_map',
                    'step_status_id', 'is_completed', 'modified_at']
    raw_id_fields = ('step_status_id', 'stu_cohort_map',)
    list_filter = ('is_completed', 'step_status_id')
    inlines = [StudentActionItemTrackerInline, CohortStepTrackerDetailsInline]


@admin.register(models.CohortStepTrackerDetails)
class CohortStepTrackerDetailsAdmin(admin.ModelAdmin):
    raw_id_fields = ('cohort_step_tracker',)
    exclude = ["created_by", "modified_by"]
    list_display = ["cohort_step_tracker", "last_commented_date_time",
                    "modified_at", 'step_completion', 'total_comments']
    list_filter = (('modified_at', DateRangeFilter),)


class StudentActionItemFilesInline(admin.TabularInline):
    model = models.StudentActionItemFiles
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_file',
              'uploaded_file', 'is_completed', 'click_on')
    readonly_fields = ['action_item_track', 'action_item_file',
                       'uploaded_file', 'is_completed', 'click_on']
    raw_id_fields = ('action_item_track', 'action_item_file',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentActionItemLinksInline(admin.TabularInline):
    model = models.StudentActionItemLinks
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_link',
              'is_completed', 'link_to_itemLInks')
    readonly_fields = ['action_item_track',
                       'action_item_link', 'is_completed', 'link_to_itemLInks']
    extra = 0
    raw_id_fields = ('action_item_track', 'action_item_link',)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentActionItemDiaryInline(admin.TabularInline):
    model = models.StudentActionItemDiary
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_diary', 'answer', 'is_completed',
              'email', 'step_title', 'cohort_name', 'link_to_studentactionitemdiary')
    readonly_fields = ['action_item_track', 'action_item_diary', 'answer', 'is_completed',
                       'email', 'step_title', 'cohort_name', 'link_to_studentactionitemdiary',]
    raw_id_fields = ('action_item_track', 'action_item_diary',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentActionItemExitTicketInline(admin.TabularInline):
    model = models.StudentActionItemExitTicket
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_exit_ticket',
              'answer', 'is_completed', 'link_to_stuactionitemexistticket')
    readonly_fields = ['action_item_track', 'action_item_exit_ticket',
                       'answer', 'is_completed', 'link_to_stuactionitemexistticket',]
    raw_id_fields = ('action_item_track', 'action_item_exit_ticket',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentActionItemTypeTableInline(admin.TabularInline):
    model = models.StudentActionItemTypeTable
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_type_table', 'answer',
              'is_completed', 'link_to_stuactionitemtypetable')
    readonly_fields = ['action_item_track', 'action_item_type_table',
                       'answer', 'is_completed', 'link_to_stuactionitemtypetable']
    raw_id_fields = ('action_item_track', 'action_item_type_table',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentActionItemFrameworkInline(admin.TabularInline):
    model = models.StudentActionItemFramework
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_framework', 'answer',
              'is_completed', 'link_to_stuactionitemframework')
    readonly_fields = ['action_item_track', 'action_item_framework',
                       'answer', 'is_completed', 'link_to_stuactionitemframework']
    raw_id_fields = ('action_item_track', 'action_item_framework',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class StudentActionItemTypeTableStep8Inline(admin.TabularInline):
    model = models.StudentActionItemTypeTableStep8
    exclude = ['created_by', 'modified_by']
    fields = ('action_item_track', 'action_item_type_table_step8', 'rating_ans',
              'comments_ans', 'is_completed', 'link_to_stuactionitemtypetablestep8')
    readonly_fields = ['action_item_track', 'action_item_type_table_step8', 'rating_ans',
                       'comments_ans', 'is_completed', 'link_to_stuactionitemtypetablestep8']
    raw_id_fields = ('action_item_track', 'action_item_type_table_step8',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(models.StudentActionItemTracker)
class StudentActionItemTrackerAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['Action_item_track_id',
                    'step_tracker', 'ActionItem', 'is_completed']
    list_filter = ['is_completed', 'ActionItem']
    raw_id_fields = ('step_tracker', 'ActionItem')
    inlines = [StudentActionItemFilesInline, StudentActionItemLinksInline, StudentActionItemDiaryInline, StudentActionItemExitTicketInline,
               StudentActionItemTypeTableInline, StudentActionItemTypeTableStep8Inline, StudentActionItemFrameworkInline]


@admin.register(models.StudentActionItemTypeTable)
class StudentActionItemTypeTableAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_item_track',
                    'action_item_type_table', 'answer', 'is_completed']
    raw_id_fields = ('action_item_track', 'action_item_type_table')


@admin.register(models.StudentActionItemFramework)
class StudentActionItemFrameworkAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_item_track',
                    'action_item_framework', 'answer', 'is_completed']
    raw_id_fields = ('action_item_track', 'action_item_framework')


@admin.register(models.StudentActionItemGoogleForm)
class StudentActionItemGoogleFormAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_item_track',
                    'action_item_google_form', 'answer', 'is_completed']
    raw_id_fields = ('action_item_track', 'action_item_google_form')


@admin.register(models.StudentActionItemTypeTableStep8)
class StudentActionItemTypeTableStep8Admin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['action_item_track', 'action_item_type_table_step8',
                    'rating_ans', 'comments_ans', 'is_completed']
    raw_id_fields = ('action_item_track', 'action_item_type_table_step8')


@admin.register(models.StudentActionItemFiles)
class StudentActionItemFilesAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item_track',
                    'action_item_file', 'uploaded_file', 'is_completed']
    list_filter = ['is_completed']
    raw_id_fields = ('action_item_track', 'action_item_file')


@admin.register(models.StudentActionItemLinks)
class StudentActionItemLinksAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item_track',
                    'action_item_link', 'is_completed']
    list_filter = ['is_completed']
    raw_id_fields = ('action_item_track', 'action_item_link')


@admin.register(models.StudentActionItemDiary)
class StudentActionItemDiaryAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'cohort_name', 'step_title', 'email', 'action_item_track',
                    'action_item_diary', 'answer', 'is_completed']
    list_filter = ('cohort_name', 'step_title', 'email', 'is_completed')
    search_fields = ('email', )
    raw_id_fields = ('action_item_track', 'action_item_diary')


@admin.register(models.StudentActionItemExitTicket)
class StudentActionItemExitTicketAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'action_item_track',
                    'action_item_exit_ticket', 'answer', 'is_completed']
    list_filter = ('is_completed',)
    search_fields = ('email',)
    raw_id_fields = ('action_item_track', 'action_item_exit_ticket')


class StudentPersonalityTestInline(admin.TabularInline):
    model = models.StudentPersonalityTest
    exclude = ['created_by', 'modified_by']
    fields = ('id', 'stu_pt_mapper', 'pt_question',
              'pt_answer', 'is_completed', 'stu_pt_test')
    readonly_fields = ('id', 'stu_pt_mapper', 'pt_question',
                       'pt_answer', 'is_completed', 'stu_pt_test')
    raw_id_fields = ('stu_pt_mapper', 'pt_question',)
    extra = 0

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(models.StudentPersonalityTestMapper)
class StudentPersonalityTestMapperAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'personality_test',
                    'student', 'student__username', 'session_id', 'last_answered', 'is_created_by_loggedin_user', 'is_completed']
    # search_fields = ('student__username',)
    raw_id_fields = ('student',)
    list_filter = ('is_completed', 'is_created_by_loggedin_user')
    search_fields = ('student__email', 'session_id',)
    raw_id_fields = ('personality_test', 'student',)
    inlines = [StudentPersonalityTestInline,]


@admin.register(models.StudentPersonalityTest)
class StudentPersonalityTestAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'stu_pt_mapper',
                    'pt_question', 'pt_answer', 'is_completed']
    list_filter = ('is_completed',)
    raw_id_fields = ('stu_pt_mapper', 'pt_question',)


@admin.register(models.Todos)
class TodosAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student', 'title', 'description', 'dated']
    list_filter = ['is_deleted', ('dated', DateRangeFilter)]


@admin.register(models.PersonNotification)
class PersonNotificationAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ('person', 'notification_type', 'created_at')
    list_filter = ['notification_type', ('created_at', DateRangeFilter)]


@admin.register(models.Stu_Notification)
class Stu_NotificationAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student', 'notification', 'title', 'isread']
    list_filter = ['isread', 'type']


@admin.register(models.Query)
class QueryAdmin(admin.ModelAdmin):

    fields = ["person", 'message', 'status', 'modified_at', 'created_at']
    list_display = ("person", "message", 'status', 'created_at')
    search_fields = ['message', 'status']
    list_filter = ['status', ('created_at', DateRangeFilter)]

    def has_add_permission(self, request):
        return True

    def has_delete_permission(self, request, obj=None):
        return True

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ["person", 'message', 'status', 'modified_at', 'created_at']
        else:
            return []

# @admin.register(models.GenerateNotificationBar)
# class GeneralNotificationBarAdmin(admin.ModelAdmin):
#     list_display = ['id', 'notification', 'is_active', 'start_date', 'end_date', 'country']
#     list_filter = ['is_active', 'country']
#     search_fields = ['country', 'notification']


# @admin.register(models.ReadGenerateNotificationBar)
# class ReadGenerateNotificationBarAdmin(admin.ModelAdmin):
#     list_display = ['id', 'student', 'gen_noti_bar', 'is_visible_marked']
#     list_filter = ['student__username']

@admin.register(models.StudentWebinarRecord)
class StudentWebinarRecordAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student__person__username',
                    'student', 'webinar', 'status']
    list_filter = ['status', 'webinar']


@admin.register(models.StudentPCTORecord)
class StudentPCTORecordAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student__person__username', 'student',
                    'webinar', 'pcto_hours', 'pcto_hour_source']
    list_filter = ['webinar', 'pcto_hour_source']
    raw_id_fields = ('student', 'webinar')


@admin.register(models.StudentProgressDetail)
class StudentProgressDetailAdmin(RelatedFieldAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['student__person__username', 'endurance_score',
                    'confidence_score', 'awareness_score', 'curiosity_score']
    raw_id_fields = ('student',)


@admin.register(models.StudentFaq)
class StudentFaqAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'locale']
    list_filter = ['locale',]


@admin.register(models.CertificateDownload)
class CertificateDownloadAdmin(RelatedFieldAdmin):
    list_display = ['student', 'created_at']







