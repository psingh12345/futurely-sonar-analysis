from django.forms.widgets import Textarea
from django.db import models
from courses import models as courseMdl
from userauth import models as authMdl
import os
import datetime
from django.utils import timezone
from django.urls import reverse
from django.utils.html import format_html
from ckeditor.fields import RichTextField
from django.utils.translation import ugettext as _


# Create your models here.

CHOICE_Lang = [
    ("en-us", "English"),
    ("it", "Italiano")
]

QUERY_STATUS_CHOICES = [
    ("Open", ("Open")),
    ("Closed", ("Closed")),
]
CHOICE_TRIAL_PLANS = (
    ("Community_to_Premium", "Community_to_Premium"),
    ("Community_to_Elite", "Community_to_Elite"),
    ("Premium_to_Elite", "Premium_to_Elite"),
)


class PlansManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(is_current_active_plan=True)

    def lang_code(self, lang):
        return super(PlansManager, self).get_queryset().filter(plan_lang=lang)


class StudentsPlanMapper(courseMdl.LogBaseModel):
    student = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="studentPlans")
    plans = models.ForeignKey(
        courseMdl.OurPlans, on_delete=models.CASCADE, related_name="studentPlans")
    plan_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    is_trial_active = models.BooleanField(default=False, blank=True, null=True)
    is_trial_expired = models.BooleanField(
        default=False, blank=True, null=True)
    trial_type = models.CharField(
        max_length=20, default='', blank=True, null=True, choices=CHOICE_TRIAL_PLANS)
    trail_days = models.IntegerField(default=7, null=True, blank=True)
    trial_start_date = models.DateTimeField(default=timezone.now)
    trial_end_date = models.DateTimeField(default=timezone.now)
    objects = models.Manager()  # The default manager.
    plansManager = PlansManager()  # Our custom manager.
    is_current_active_plan = models.BooleanField(
        default=True, blank=True, null=True)

    def link_to_studentplanmapper(self):
        link = reverse(
            "admin:student_studentsplanmapper_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')

    class Meta:
        verbose_name = 'StudentsPlanMapper'
        verbose_name_plural = 'StudentsPlanMapper'

    def __str__(self):
        return f"{self.student}-{self.plans}"


class StuCohortManager(models.Manager):
    def lang_code(self, lang):
        return super(StuCohortManager, self).get_queryset().filter(stu_cohort_lang=lang)


class StudentCohortMapper(courseMdl.LogBaseModel):
    stu_cohort_map_id = models.BigAutoField(primary_key=True)
    student = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="stuMapID")
    cohort = models.ForeignKey(
        courseMdl.Cohort, on_delete=models.CASCADE, related_name="cohortMapID")
    stu_cohort_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    objects = models.Manager()  # The default manager.
    stuCohortManager = StuCohortManager()  # Our custom manager.
    is_completed = models.BooleanField(default=False, blank=True, null=True)
    student_plan = models.ForeignKey(
        StudentsPlanMapper, on_delete=models.CASCADE, related_name="stu_cohort_map", blank=True, null=True)

    def link_to_studentcohortmapper(self):
        link = reverse("admin:student_studentcohortmapper_change",
                       args=[self.stu_cohort_map_id])
        return format_html(f'<a href="{link}" target="_blank">click here</a>')

    @property
    def is_cohort_completed(self):
        stu_steps = self.stu_cohort_map.all()
        completed = 0
        for stu_step in stu_steps:
            if (stu_step.is_completed == True):
                completed = completed+1
        if completed == 0:
            return False
        if (completed >= stu_steps.count()-1):
            return True
        else:
            return False
    
    def is_cohort_started(self):
        stu_steps = self.stu_cohort_map.all()
        is_cohort_started_var = False
        for stu_step in stu_steps:
            if stu_step.tot_completed > 0:
                is_cohort_started_var = True
                break
        return is_cohort_started_var

    @property
    def cohort_completion_percentage(self):
        stu_steps = self.stu_cohort_map.all().count()
        stu_completed_steps = self.stu_cohort_map.filter(
            is_completed=True).count()
        if stu_steps == 0:
            return 0
        return int(stu_completed_steps*100/stu_steps)
    
    @property
    def cohort_completion_percentage_for_counselor(self):
        stu_linked_steps = self.stu_cohort_map.all()
        stu_steps = stu_linked_steps.count()
        stu_completed_steps = 0
        if stu_steps == 0:
            return 0
        stu_unlocked_steps = 0
        for stu_linked_step in stu_linked_steps:
            if stu_linked_step.step_status_id.is_active:
                stu_unlocked_steps += 1
                if stu_linked_step.is_step_50_percentage_completed:
                    stu_completed_steps += 1
        try:
            cohort_completion_percentage = int(stu_completed_steps*100/stu_unlocked_steps)
        except:
            cohort_completion_percentage = 0
        return cohort_completion_percentage

    @property
    def is_cohort_75_percentage_completed_of_unlocked_steps(self):
        stu_linked_steps = self.stu_cohort_map.all()
        stu_completed_steps = 0
        stu_unlocked_steps = 0
        for stu_linked_step in stu_linked_steps:
            if stu_linked_step.step_status_id.is_active:
                stu_unlocked_steps = stu_unlocked_steps + 1
                if stu_linked_step.is_step_75_percentage_completed:
                    stu_completed_steps = stu_completed_steps+1
        # stu_completed_steps = self.stu_cohort_map.filter(is_step_75_percentage_completed=True).count()
        try:
            completed_percentage = stu_completed_steps * 100 / stu_unlocked_steps
            if completed_percentage >= 75:
                return True
            else:
                return False
        except:
            return False
        
    @property
    def is_cohort_50_percentage_completed_of_unlocked_steps(self):
        stu_linked_steps = self.stu_cohort_map.all()
        stu_completed_steps = 0
        stu_unlocked_steps = 0
        for stu_linked_step in stu_linked_steps:
            if stu_linked_step.step_status_id.is_active_2weeks_ago:
                stu_unlocked_steps = stu_unlocked_steps + 1
                if stu_linked_step.is_step_50_percentage_completed:
                    stu_completed_steps = stu_completed_steps+1
        try:
            completed_percentage = stu_completed_steps * 100 / stu_unlocked_steps
            if completed_percentage >= 50:
                return True
            else:
                return False
        except:
            return False

    @property
    def total_unlocked_steps(self):
        stu_steps = self.stu_cohort_map.all()
        stu_unlocked_steps = 0
        for stu_step in stu_steps:
            if stu_step.step_status_id.is_active:
                stu_unlocked_steps = stu_unlocked_steps+1
        return stu_unlocked_steps

    @property
    def is_eligible_for_pcto_hour(self):
        stu_steps = self.stu_cohort_map.all()
        completed = 0
        for stu_step in stu_steps:
            if (stu_step.is_completed == True):
                completed = completed+1
        if completed == 0:
            return False
        if (completed >= 8):
            return True
        else:
            return False
    
    def is_any_pending_diary_comment_to_read(self):
        result = False
        stu_steps = self.stu_cohort_map.all()
        for step in stu_steps:
            step_comment_read_status = step.is_any_pending_comment_to_read()
            if step_comment_read_status is True:
                result = True
                break
        return result



    class Meta:
        # ordering = ['cohort__module__module_priority']
        verbose_name = 'StudentCohortMapper'
        verbose_name_plural = 'StudentCohortMapper'

    def __str__(self):
        return f"{self.student}-{self.cohort}"


class CohortStepTracker(courseMdl.LogBaseModel):
    step_track_id = models.BigAutoField(primary_key=True)
    stu_cohort_map = models.ForeignKey(
        StudentCohortMapper, on_delete=models.CASCADE, related_name="stu_cohort_map")
    step_status_id = models.ForeignKey(
        courseMdl.step_status, on_delete=models.CASCADE, related_name="step_status_id")
    is_completed = models.BooleanField(default=False)
    # last_commented_date_time = models.DateTimeField(default=timezone.now)

    def link_to_cohortstep_tracker(self):
        link = reverse("admin:student_cohortsteptracker_change",
                       args=[self.step_track_id])
        return format_html(f'<a href="{link}" target="_blank">{self.stu_cohort_map}</a>')

    @property
    def tot_completed(self):
        ac_items = self.stu_action_items.filter(
            ActionItem__is_deleted=False).exclude(ActionItem__action_type__datatype="Exit").all()
        completed = 0
        for ai in ac_items:
            if (ai.is_completed == True):
                completed = completed+1
        return completed
    
    # @property
    # def tot_completed(self):
    #     ac_items = self.stu_action_items.filter(
    #         ActionItem__is_deleted=False).all()
    #     completed = 0
    #     for ai in ac_items:
    #         if (ai.is_completed == True):
    #             completed = completed+1
    #     return completed

    @property
    def total_diary_comments_count(self):
        total_count = self.stu_action_items.filter(
            action_item_diary_track__comments_student_actions_item_diary__is_active=True).count()
        return total_count
    
    def is_any_pending_comment_to_read(self):
        result = False
        unread_comments = self.stu_action_items.filter(
            action_item_diary_track__comments_student_actions_item_diary__is_read=False).count()
        if unread_comments > 0:
            result = True
        return result

    @property
    def is_step_completed(self):
        ac_items = self.stu_action_items.filter(
            ActionItem__is_deleted=False).exclude(ActionItem__action_type__datatype="Exit").all()
        completed = 0
        for ai in ac_items:
            if (ai.is_completed == True):
                completed = completed+1
        if (ac_items.count() == completed and completed != 0):
            return True
        else:
            return False

    # @property
    # def is_step_completed(self):
    #     ac_items = self.stu_action_items.filter(
    #         ActionItem__is_deleted=False).all()
    #     completed = 0
    #     for ai in ac_items:
    #         if (ai.is_completed == True):
    #             completed = completed+1
    #     if (ac_items.count() == completed and completed != 0):
    #         return True
    #     else:
    #         return False
    

    @property
    def is_step_75_percentage_completed(self):
        ac_items = self.stu_action_items.filter(
            ActionItem__is_deleted=False).all()
        completed = 0
        for ai in ac_items:
            if (ai.is_completed == True):
                completed = completed+1
        try:
            complated_percentage = (completed * 100) / ac_items.count()
            if (complated_percentage >= 75):
                return True
            else:
                return False
        except:
            return False
        
    @property
    def is_step_50_percentage_completed(self):
        ac_items = self.stu_action_items.filter(
            ActionItem__is_deleted=False).all()
        completed = 0
        for ai in ac_items:
            if (ai.is_completed == True):
                completed = completed+1
        try:
            complated_percentage = (completed * 100) / ac_items.count()
            if (complated_percentage >= 50):
                return True
            else:
                return False
        except:
            return False

    @property
    def is_first_action_item_completed(self):
        ac_items = self.stu_action_items.exclude(
            ActionItem__action_type__datatype="Exit")
        completed = 0
        for ai in ac_items:
            if (ai.is_completed == True):
                completed = completed+1
                break
        if (completed > 0):
            return True
        else:
            return False

    @property
    def get_diary(self):
        diary = []
        ac_items = self.stu_action_items.all()
        for ai in ac_items:
            if (ai.ActionItem.action_type.datatype == "Diary"):
                diary.append(ai.action_item_diary_track.all())
        return diary
    
    class Meta:
        ordering = ['step_status_id__step__step_sno']
        verbose_name = 'CohortStepTracker'
        verbose_name_plural = 'CohortStepTracker'

    def __str__(self):
        return f"{self.stu_cohort_map}"


class CohortStepTrackerDetails(courseMdl.LogBaseModel):
    cohort_step_tracker = models.OneToOneField(
        CohortStepTracker, on_delete=models.CASCADE, related_name="cohort_step_tracker_details")
    last_commented_date_time = models.DateTimeField(default=timezone.now)
    step_completion = models.IntegerField(default=0)
    total_comments = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'CohortStepTrackerDetail'
        verbose_name_plural = 'CohortStepTrackerDetails'


class StudentProgressDetail(courseMdl.LogBaseModel):
    student = models.OneToOneField(
        authMdl.Student, on_delete=models.CASCADE, related_name="student_endurance_score")
    endurance_score = models.IntegerField(default=0)
    confidence_score = models.IntegerField(default=0)
    awareness_score = models.IntegerField(default=0)
    curiosity_score = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'StudentProgressDetail'
        verbose_name_plural = 'StudentsProgressDetail'

    def __str__(self):
        return f"{self.student}"


class StudentActionItemTracker(courseMdl.LogBaseModel):
    Action_item_track_id = models.BigAutoField(primary_key=True)
    step_tracker = models.ForeignKey(
        CohortStepTracker, on_delete=models.CASCADE, related_name="stu_action_items")
    ActionItem = models.ForeignKey(
        courseMdl.ActionItems, on_delete=models.CASCADE, related_name="action_item_track")
    is_completed = models.BooleanField(default=False)

    def link_to_studentactionitemtracker(self):
        link = reverse('admin:student_studentactionitemtracker_change', args=[
                       self.Action_item_track_id])
        return format_html(f'<a href="{link}" target="_blank">Click Here</a>')

    class Meta:
        ordering = ['ActionItem__action_sno']
        verbose_name = 'StudentActionItemTracker'
        verbose_name_plural = 'StudentActionItemTracker'

    @property
    def is_action_item_completed(self):
        action_item_type = self.ActionItem.action_type.datatype
        if (action_item_type == "Links"):
            ac_items = self.action_item_link_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        elif (action_item_type == "Diary"):
            ac_items = self.action_item_diary_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        elif (action_item_type == "Exit"):
            ac_items = self.action_item_exit_ticket_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        elif (action_item_type == "Table"):
            ac_items = self.action_item_type_table_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        elif (action_item_type == "TableStep8"):
            ac_items = self.action_item_type_table_step8_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        elif (action_item_type == "Google_Form"):
            ac_items = self.action_item_google_form_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        elif (action_item_type == "Framework"):
            ac_items = self.action_item_framework_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        else:
            ac_items = self.action_item_file_track.filter(
                action_item_track__ActionItem__is_deleted=False).all()
        completed = 0
        for ai in ac_items:
            if (ai.is_completed == "Yes"):
                completed = completed+1
        if (ac_items.count() == completed):
            return True
        else:
            return False

    def __str__(self):
        return f"{self.step_tracker}-{self.ActionItem}"


def content_file_name(instance, filename):
    ext = filename.split('.')[-1]
    fn = filename.split('.')[0]
    print(fn)
    dt = datetime.datetime.now()
    dt = dt.timestamp()
    dt = int(dt)
    filename = f"{instance.action_item_track.ActionItem.action_id}_{instance.action_item_track.step_tracker.stu_cohort_map.student.id}_{instance.id}_{fn}_{dt}.{ext}"
    # filename = "%s_%s.%s" % (instance.user.id, instance.questid.id, ext)
    # return os.path.join("stu_files", filename)
    return os.path.join("stu_files/course_step_actionitem", filename)


class StudentActionItemFiles(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_file_track")
    action_item_file = models.ForeignKey(
        courseMdl.ActionItemFiles, on_delete=models.CASCADE, related_name="stu_action_item_file")
    uploaded_file = models.FileField(
        upload_to=content_file_name, blank=True, null=True)
    file_answer = models.TextField(blank=True, null=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def click_on(self):
        link = reverse(
            'admin:student_studentactionitemfiles_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">click here</a>')

    class Meta:
        ordering = ('action_item_file__sno',)
        verbose_name = 'StudentActionItemFiles'
        verbose_name_plural = 'StudentActionItemFiles'

    def __str__(self):
        return f"{self.id}:{self.action_item_track}-{self.action_item_file}"


class StudentActionItemLinks(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_link_track")
    action_item_link = models.ForeignKey(
        courseMdl.ActionItemLinks, on_delete=models.CASCADE, related_name="stu_action_item_link")
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def link_to_itemLInks(self):
        link = reverse(
            'admin:student_studentactionitemlinks_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        ordering = ('action_item_link__sno',)
        verbose_name = 'StudentActionItemLinks'
        verbose_name_plural = 'StudentActionItemLinks'

    def __str__(self):
        return f"{self.id}:{self.action_item_track}-{self.action_item_link}"


class StudentActionItemDiary(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_diary_track")
    action_item_diary = models.ForeignKey(
        courseMdl.ActionItemDiary, on_delete=models.CASCADE, related_name="stu_action_item_diary")
    answer = models.TextField(default='', blank=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)
    email = models.CharField(max_length=150, blank=True, null=True)
    step_title = models.CharField(max_length=500, blank=True, null=True)
    cohort_name = models.CharField(max_length=100, blank=True, null=True)

    def link_to_studentactionitemdiary(self):
        link = reverse(
            'admin:student_studentactionitemdiary_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    @property
    def last_commented_diary_date(self):
        comment = self.comments_student_actions_item_diary.all().order_by("-created_at").first()
        if comment:
            return comment.created_at
        else:
            return self.modified_at
    # @property
    # def email(self):
    #     email = self.action_item_track.step_tracker.stu_cohort_map.student.email
    #     return email

    # @property
    # def step_title(self):
    #     step_title = self.action_item_track.step_tracker.step_status_id.step.title
    #     return step_title

    # @property
    # def cohort_name(self):
    #     cohort_name = self.action_item_track.step_tracker.stu_cohort_map.cohort.cohort_name
    #     return cohort_name

    class Meta:
        ordering = ('action_item_diary__sno',)
        verbose_name = 'StudentActionItemDiary'
        verbose_name_plural = 'StudentActionItemDiary'

    def __str__(self):
        return f"{self.id}:{self.action_item_track}-{self.action_item_diary}"


class StudentActionItemDiaryComment(courseMdl.LogBaseModel):
    person = models.ForeignKey(authMdl.Person, on_delete=models.CASCADE,
                               related_name="student_comments")  # Commenting Person
    student_actions_item_diary_id = models.ForeignKey(
        StudentActionItemDiary, on_delete=models.CASCADE, related_name="comments_student_actions_item_diary")
    comment = models.TextField()
    is_active = models.BooleanField(default=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'StudentActionItemDiaryComment'
        verbose_name_plural = 'StudentActionItemDiaryComments'

    def __str__(self):
        return f"{self.person}"


class StudentActionItemDiaryAIComment(courseMdl.LogBaseModel):
    AI_COMMENT_STATUS_CHOICES = (
        ('Generated', ('Generated')),
        ('Published', ('Published')),
        ('Cancelled', ('Cancelled')),
        ('Modified Published', ('Modified Published')),
    )

    student_actions_item_diary_id = models.ForeignKey(
        StudentActionItemDiary, on_delete=models.CASCADE, related_name="ai_comments_student_actions_item_diary")
    ai_comment = models.TextField()
    ai_comment_status = models.CharField(
        max_length=20, choices=AI_COMMENT_STATUS_CHOICES, default='Generated')

    class Meta:
        ordering = ('created_at',)
        verbose_name = 'StudentActionItemDiaryAIComment'
        verbose_name_plural = 'StudentActionItemDiaryAIComments'

    def __str__(self):
        return f"{self.id}"


class StudentActionItemExitTicket(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_exit_ticket_track")
    action_item_exit_ticket = models.ForeignKey(
        courseMdl.ActionItemExitTicket, on_delete=models.CASCADE, related_name="stu_action_item_exit_ticket")
    answer = models.TextField(default='', blank=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def link_to_stuactionitemexistticket(self):
        link = reverse(
            'admin:student_studentactionitemexitticket_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        ordering = ['action_item_exit_ticket__sno']
        verbose_name = 'StudentActionItemExitTicket'
        verbose_name_plural = 'StudentActionItemExitTickets'


class StudentActionItemTypeTable(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_type_table_track")
    action_item_type_table = models.ForeignKey(
        courseMdl.ActionItemTypeTable, on_delete=models.CASCADE, related_name="stu_action_item_type_table")
    answer = models.JSONField(default=dict, blank=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def link_to_stuactionitemtypetable(self):
        link = reverse(
            'admin:student_studentactionitemtypetable_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        ordering = ['action_item_type_table__sno']
        verbose_name = 'StudentActionItemTypeTable'
        verbose_name_plural = 'StudentActionItemTypeTables'


class NoSortJSONField(models.TextField):
    def formfield(self, **kwargs):
        # Use the custom widget for the JSON field
        kwargs['widget'] = Textarea(attrs={'rows': 10})
        return super().formfield(**kwargs)


class StudentActionItemFramework(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_framework_track")
    action_item_framework = models.ForeignKey(
        courseMdl.ActionItemFramework, on_delete=models.CASCADE, related_name="stu_action_framework")
    # answer = models.JSONField(default=dict, blank=True)
    answer = NoSortJSONField(blank=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def link_to_stuactionitemframework(self):
        link = reverse(
            'admin:student_studentactionitemframework_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        ordering = ['action_item_framework__sno']
        verbose_name = 'StudentActionItemFramework'
        verbose_name_plural = 'StudentActionItemFrameworks'


class StudentActionItemGoogleForm(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_google_form_track")
    action_item_google_form = models.ForeignKey(
        courseMdl.ActionItemGoogleForm, on_delete=models.CASCADE, related_name="stu_action_item_google_form")
    answer = models.TextField(default='', blank=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def link_to_stuactionitemgoogleform(self):
        link = reverse(
            'admin:student_studentactionitemgoogleform_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Google Form</a>')

    class Meta:
        ordering = ['action_item_google_form__sno']
        verbose_name = 'StudentActionItemGoogleForm'
        verbose_name_plural = 'StudentActionItemGoogleForms'


class StudentActionItemTypeTableStep8(courseMdl.LogBaseModel):
    action_item_track = models.ForeignKey(
        StudentActionItemTracker, on_delete=models.CASCADE, related_name="action_item_type_table_step8_track")
    action_item_type_table_step8 = models.ForeignKey(
        courseMdl.ActionItemTypeTableStep8, on_delete=models.CASCADE, related_name="stu_action_item_type_table_step8")
    rating_ans = models.IntegerField(default=0, null=True, blank=True)
    comments_ans = models.TextField(default='', blank=True)
    is_completed = models.CharField(
        max_length=3, default='No', blank=True, choices=courseMdl.CHOICE_IS_Active)

    def link_to_stuactionitemtypetablestep8(self):
        link = reverse(
            'admin:student_studentactionitemtypetablestep8_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        ordering = ['action_item_type_table_step8__sno']
        verbose_name = 'StudentActionItemTypeTableStep8'
        verbose_name_plural = 'StudentActionItemTypeTableStep8'


SCHOLARSHIP_STATUS = [
    ("Applied", "Applied"),
    ("Approved", "Approved"),
    ("Declined", "Declined"),
]


class StudentScholarshipTestMapper(courseMdl.LogBaseModel):
    scholarship_test = models.ForeignKey(
        courseMdl.ScholarshipTest, on_delete=models.CASCADE, related_name="stu_scholarship_test_mapper", default='')
    student = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="stu_scholarship_test_mapper")
    last_answered = models.IntegerField(default=0, null=True, blank=True)
    is_applied = models.BooleanField(default=False)
    lang_code = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    status = models.CharField(
        max_length=20, default="Applied", blank=True, choices=SCHOLARSHIP_STATUS)

    @property
    def tot_ques_completed(self):
        count = self.stu_scholarship_test_ques.filter(
            is_completed=True).count()
        return count

    @property
    def tot_question(self):
        count = self.stu_scholarship_test_ques.all().count()
        return count

    @property
    def is_stu_scholarship_test_completed(self):
        tot_completed = self.stu_scholarship_test_ques.filter(
            is_completed=True).count()
        tot_question = self.stu_scholarship_test_ques.all().count()
        if (tot_completed == tot_question):
            return True
        else:
            return False

    class Meta:
        verbose_name = "StudentScholarshipTestMapper"
        verbose_name_plural = "StudentsScholarshipTestMapper"


class StudentScholarShipTest(courseMdl.LogBaseModel):
    stu_scholarshipTest_mapper = models.ForeignKey(
        StudentScholarshipTestMapper, on_delete=models.CASCADE, related_name="stu_scholarship_test_ques", default='')
    scholarshipTest_question = models.ForeignKey(
        courseMdl.ScholarshipTestQuestion, on_delete=models.CASCADE, related_name="stu_scholarship_test_ques", default='')
    scholarshipTest_answer = models.CharField(
        max_length=250, default='', null=True, blank=True)
    is_completed = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = "StudentScholarShipTest"
        verbose_name_plural = "StudentsScholarShipTest"


class StudentPersonalityTestMapper(courseMdl.LogBaseModel):
    personality_test = models.ForeignKey(
        courseMdl.PersonalityTest, on_delete=models.CASCADE, related_name="stu_ptest_mapper")
    student = models.ForeignKey(authMdl.Person, on_delete=models.CASCADE,
                                related_name="person_ptest_mapper", blank=True, null=True)
    session_id = models.CharField(max_length=200, default="", blank=True)
    is_created_by_loggedin_user = models.BooleanField(default=True)
    last_answered = models.IntegerField(default=0, null=True, blank=True)
    is_completed = models.BooleanField(default=False, null=True, blank=True)
    lang_code = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)

    @property
    def tot_ques_completed(self):
        count = self.stu_ptest.filter(is_completed=True).count()
        return count

    @property
    def tot_question(self):
        count = self.stu_ptest.all().count()
        return count

    @property
    def is_pt_completed(self):
        tot_completed = self.stu_ptest.filter(is_completed=True).count()
        tot_question = self.stu_ptest.all().count()
        if (tot_completed == tot_question):
            return True
        else:
            return False

    @property
    def calculate_my_score(self):
        result = {}
        result[("R", "Realistic")] = self.stu_ptest.filter(
            pt_answer="Agree", pt_question__category="Realistic").count()
        result[("I", "Investigative")] = self.stu_ptest.filter(
            pt_answer="Agree", pt_question__category="Investigative").count()
        result[("A", "Artistic")] = self.stu_ptest.filter(
            pt_answer="Agree", pt_question__category="Artistic").count()
        result[("S", "Social")] = self.stu_ptest.filter(
            pt_answer="Agree", pt_question__category="Social").count()
        result[("E", "Enterprising")] = self.stu_ptest.filter(
            pt_answer="Agree", pt_question__category="Enterprising").count()
        result[("C", "Conventional")] = self.stu_ptest.filter(
            pt_answer="Agree", pt_question__category="Conventional").count()
        return result

    class Meta:
        verbose_name = 'StudentPersonalityTestMapper'
        verbose_name_plural = 'StudentsPersonalityTestMapper'

    def __str__(self):
        return f"<Student Personality Test Mapper : {self.student} >"


class StudentPersonalityTest(courseMdl.LogBaseModel):
    stu_pt_mapper = models.ForeignKey(
        StudentPersonalityTestMapper, on_delete=models.CASCADE, related_name="stu_ptest")
    pt_question = models.ForeignKey(
        courseMdl.PersonalityTestQuestion, on_delete=models.CASCADE, related_name="stu_ptest_question")
    pt_answer = models.CharField(
        max_length=20, default='', null=True, blank=True)
    is_completed = models.BooleanField(default=False, null=True, blank=True)

    def stu_pt_test(self):
        link = reverse(
            'admin:student_studentpersonalitytest_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        verbose_name = 'StudentPersonalityTest'
        verbose_name_plural = 'StudentsPersonalityTests'


class TodosManager(models.Manager):
    def get_queryset(self):
        return super(TodosManager, self).get_queryset().filter(is_deleted=False)


class Todos(courseMdl.LogBaseModel):
    student = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="todos")
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True, default='')
    dated = models.DateField()
    is_deleted = models.BooleanField(default=False)
    objects = TodosManager()

    def todos(self):
        link = reverse('admin:student_todos_change', args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    class Meta:
        verbose_name = 'Todo'
        verbose_name_plural = 'Todos'

    def __str__(self):
        return f"{self.title}"


class PersonNotification(courseMdl.LogBaseModel):
    """This model is used to store acivated/checked notification types by any person """
    person = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="person_notifications")
    notification_type = models.ForeignKey(
        courseMdl.Notification_type, on_delete=models.CASCADE, related_name="person_notifications")

    class Meta:
        verbose_name = 'PersonNotification'
        verbose_name_plural = 'PersonNotifications'

    def __str__(self):
        return "{} - {}".format(self.person, self.notification_type)


class Stu_Notification(courseMdl.LogBaseModel):
    student = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="my_notifications")
    notification = models.ForeignKey(
        courseMdl.Notification, on_delete=models.CASCADE, related_name="stu_notifications", blank=True, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    type = models.CharField(
        max_length=15, default='General', blank=True, null=True)
    isread = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Student_Notification'
        verbose_name_plural = 'Student_Notifications'

    def __str__(self):
        return f"{self.title}"


class Query(courseMdl.LogBaseModel):
    person = models.ForeignKey(
        authMdl.Person, related_name="student_queries", on_delete=models.CASCADE)
    message = models.TextField(default='', blank=True)
    status = models.CharField(
        max_length=50, default='Open', blank=True, choices=QUERY_STATUS_CHOICES)

    class Meta:
        verbose_name = 'Query'
        verbose_name_plural = 'Queries'

    def __str__(self):
        return "{} | {}".format(self.person, self.status)


# COUNTRY_CHOICE = [
#     ("US", "English"),
#     ("it", "Italiano")
# ]

# class GenerateNotificationBar(courseMdl.LogBaseModel):
#     notification = models.CharField(max_length=600, null=True, blank=True)
#     is_active = models.BooleanField(default=False)
#     start_date = models.DateTimeField(default=timezone.now)
#     end_date = models.DateTimeField(default=timezone.now)
#     country = models.CharField(max_length=10, default="US", choices=COUNTRY_CHOICE)

#     class Meta:
#         verbose_name = 'GenerateNotificationBar'
#         verbose_name_plural = 'GenerateNotificationsBar'

#     def __str__(self):
#         return "{}".format(self.notification)

# class ReadGenerateNotificationBar(courseMdl.LogBaseModel):
#     student = models.ForeignKey(authMdl.Person, on_delete=models.CASCADE, related_name="read_notification_bar")
#     gen_noti_bar = models.ForeignKey(GenerateNotificationBar, on_delete=models.CASCADE)
#     is_visible_marked = models.BooleanField(default=False)

#     class Meta:
#         verbose_name = 'ReadGenerateNotificationBar'
#         verbose_name_plural = 'ReadGenerateNotificationsBar'

#     def __str__(self):
#         return "{}".format(self.student)

CHOICE_STATUS_STU_WEBINAR = [
    ("Registered", "Registered"),
    ("Attended", "Attended")
]


class StudentWebinarRecord(courseMdl.LogBaseModel):
    student = models.ForeignKey(
        authMdl.Student, related_name="student_webinar_record", on_delete=models.CASCADE)
    webinar = models.ForeignKey(
        courseMdl.Webinars, related_name="student_webinar_record", on_delete=models.CASCADE)
    # is_webinar_completed = models.BooleanField(default=False, blank= True, null= True)
    status = models.CharField(
        max_length=50, default='Registered', blank=True, choices=CHOICE_STATUS_STU_WEBINAR)
    seat_reserve = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'StudentWebinarRecord'
        verbose_name_plural = 'StudentWebinarRecords'

    def __str__(self):
        return "{} | {}".format(self.student, self.status)


class StudentWebinarMapper(courseMdl.LogBaseModel):
    webinar_questionnaire = models.ForeignKey(
        courseMdl.WebinarQuestionnaire, related_name="stu_webinar_test_mapper", on_delete=models.CASCADE)
    student = models.ForeignKey(
        authMdl.Person, related_name="stu_webinar_test_mapper", on_delete=models.CASCADE)
    webinar = models.ForeignKey(
        courseMdl.Webinars, on_delete=models.CASCADE, related_name="stu_webinar")
    lang_code = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'StudentWebinarMapper'
        verbose_name_plural = 'StudentWebinarsMapper'


class StudentWebinarAnswer(courseMdl.LogBaseModel):
    stu_webinar_mapper = models.ForeignKey(
        StudentWebinarMapper, on_delete=models.CASCADE, related_name="stu_webinar_test")
    webinar_question = models.ForeignKey(
        courseMdl.WebinarQuestion, on_delete=models.CASCADE, related_name="stu_webinar_question")
    webinar_answer = models.CharField(
        max_length=500, default='', null=True, blank=True)
    is_completed = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = 'StudentWebinarAnswer'
        verbose_name_plural = 'StudentWebinarAnswers'


CHOICE_PCTO_SOURCE = [
    ("Future-lab", "Future-lab"),
    ("Webinar", "Webinar"),
    ("Course-1", "Conoscenza di sé e apertura a nuove prospettive"),
    ("Course-2", "Conoscenza del mondo universitario/ITS"),
    ("Course-FS", "Conoscenza di sé e del mondo universitario/its"),
    ("Course-MS", "Orientamento verso le scuole superiori"),
    ("Job-Course", "Orientamento al lavoro"),
]


class StudentPCTORecord(courseMdl.LogBaseModel):
    student = models.ForeignKey(
        authMdl.Student, related_name="student_pcto_record", on_delete=models.CASCADE)
    webinar = models.ForeignKey(StudentWebinarRecord, related_name="student_pcto_record",
                                on_delete=models.CASCADE, null=True, blank=True)
    pcto_hours = models.IntegerField(default=0, blank=True, null=True)
    pcto_hour_source = models.CharField(
        max_length=50, default='Webinar', blank=True, choices=CHOICE_PCTO_SOURCE)

    class Meta:
        verbose_name = 'StudentPCTORecord'
        verbose_name_plural = 'StudentPCTORecords'

    def __str__(self):
        return "{} | {}".format(self.student, self.pcto_hours)


class StudentFaq(courseMdl.LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null=True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)

    class Meta:
        verbose_name = 'StudentFaq'
        verbose_name_plural = 'StudentsFaq'


class CertificateDownload(courseMdl.LogBaseModel):
    student = models.ForeignKey(
        authMdl.Student, on_delete=models.CASCADE, related_name="student_certificate_download")

    class Meta:
        verbose_name = 'CertificateDownload'
        verbose_name_plural = 'CertificateDownloads'
