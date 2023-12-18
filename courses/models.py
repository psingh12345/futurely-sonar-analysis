from email.policy import default
from urllib import response
from django.db import models
import datetime
from django.db.models.base import Model
from django.utils import timezone
from userauth import models as authMdl
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import ugettext_lazy as _
from datetime import date
import pytz
from django.conf import settings
from ckeditor.fields import RichTextField
from enum import Enum
from student.tasks import notify_students_about_job_posting
from datetime import timedelta
# Create your models here.    


class LogBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, editable=False)
    created_by = models.CharField(max_length=150, default='', blank=True)
    modified_at = models.DateTimeField(auto_now=True, editable=False)
    modified_by = models.CharField(max_length=150, default='', blank=True)

    class Meta:
        abstract = True

CHOICE_EXIT_TICKET_TYPE = [
    ('MCQ', 'MCQ'),
    ('Rating','Rating'),
    ('Checkbox', 'Checkbox'),
    ('Dropdown', 'Dropdown'),
    ('Text', 'Text'),
    ('Other', 'Other'),
]

CHOICES_GOOGLE_FORM = [
    ('MCQ', 'MCQ'),
    ('Rating','Rating'),
    ('Star', 'Star'),
    ('Dropdown', 'Dropdown'),
    ('Text', 'Text'),
    ('Other', 'Other'),
    # ('Checkbox', 'Checkbox'),
    # ('Link', 'Link'),
    # ('File', 'File'),
]

class EmailTemplate(LogBaseModel):
    template_name = models.CharField(max_length=100, blank=False, null=False)
    template_file = models.FileField(upload_to='email_template', blank=False)

    def __str__(self):
        return f"{self.template_name}"


class EmailForwadingDetails(LogBaseModel):
    excel_file = models.FileField(upload_to="excel_data", blank=False)
    emailtemplate_id = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE, related_name="exceldata")

CHOICE_Lang = [
    ("en-us", "English"),
    ("it", "Italiano")
]

class PlansManager(models.Manager):
    def lang_code(self, lang):
        return super(PlansManager, self).get_queryset().filter(plan_lang=lang)


class PlanNames(Enum):
    Community = 'Community'
    Premium = 'Premium'
    Elite = 'Elite'
    Diamond = 'Diamond'
    Trial2022 = 'Trial2022'
    FastTrack = 'FastTrack'
    MiddleSchool = 'MiddleSchool'
    JobCourse = 'JobCourse'


CHOICE_PLAN_NAMES = [
    (PlanNames.Community.value, PlanNames.Community.value),
    (PlanNames.Premium.value, PlanNames.Premium.value),
    (PlanNames.Elite.value, PlanNames.Elite.value),
    (PlanNames.Diamond.value, PlanNames.Diamond.value),
    (PlanNames.Trial2022.value, PlanNames.Trial2022.value),
    (PlanNames.FastTrack.value, PlanNames.FastTrack.value),
    (PlanNames.MiddleSchool.value, PlanNames.MiddleSchool.value),
    (PlanNames.JobCourse.value, PlanNames.JobCourse.value),
]


class OurPlans(LogBaseModel):
    plan_name = models.CharField(
        max_length=20, blank=False, null=False, choices=CHOICE_PLAN_NAMES)
    title = models.CharField(max_length=200, blank=False, null=False)
    sub_title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True)
    introduction_video = models.URLField(blank=True)
    cost = models.CharField(max_length=10, default='', blank=True)
    upgrade_cost = models.CharField(max_length=10, default='', blank=True)
    weekly_cost = models.CharField(max_length=10, default='', blank=True)
    weekly_cost_duration = models.IntegerField(default=10,blank=True, null=True)
    pcto_hour_limit = models.IntegerField(default=2,blank=True, null=True)
    trial_days = models.IntegerField(default=0, blank = True, null=True)
    is_paid_plan = models.BooleanField(default=True)
    plan_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    objects = models.Manager()  # The default manager.
    plansManager = PlansManager()  # Our custom manager.

    class Meta:
        verbose_name = 'OurPlan'
        verbose_name_plural = 'OurPlans'

    def __str__(self):
        return f"{self.title}"


class Courses(LogBaseModel):
    course_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=500, blank=False, null=False)
    description = models.TextField(default='', blank=True)
    # total_modules=models.IntegerField(blank=True,null=True)
    bg_image = models.FileField(upload_to='images', blank=True)
    duration = models.CharField(max_length=10, blank=True, default='')
    plan = models.ManyToManyField(OurPlans, related_name="course")

    @property
    def total_module(self):
        obj = self.module.all()
        for o in obj:
            print(o.description)
        return self.module.all()

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return f"{self.title}"


class ModuleManager(models.Manager):
    def get_queryset(self):
        return super(ModuleManager, self).get_queryset()

    def lang_code(self, lang):
        return super(ModuleManager, self).get_queryset().filter(module_lang=lang)


class Modules(LogBaseModel):
    module_id = models.BigAutoField(primary_key=True)
    course = models.ForeignKey(
        Courses, on_delete=models.CASCADE, related_name="module")
    title = models.CharField(max_length=500, blank=False, null=False)
    description = models.TextField(default='', blank=True)
    # total_steps=models.IntegerField(blank=True,null=True)
    bg_image = models.FileField(upload_to='images', blank=True)
    duration = models.CharField(max_length=10, blank=True, default='')
    introduction_video = models.URLField(blank=True, null=True)
    module_priority = models.IntegerField(default='0')
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    is_active = models.BooleanField(default=False)
    is_for_middle_school = models.BooleanField(default=False, blank=True, null= True)
    is_for_fast_track_program = models.BooleanField(default=False, blank=True, null= True)
    objects = models.Manager()  # The default manager.
    moduleManager = ModuleManager()  # Our custom manager
    tot_steps = models.IntegerField(blank=True, null=True, default=10)
    is_allowed_to_display_timings = models.BooleanField(default=False, blank=True, null= True)

    def link_to_module(self):
        link = reverse("admin:courses_modules_change", args=[self.module_id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')

    @property
    def count_tot_steps(self):
        tot = self.steps.exclude(is_backup_step=True).all().count()
        return tot

    @property
    def tot_action_items(self):
        tot_ai = 0
        all_steps = self.steps.exclude(is_backup_step=True).all()
        for step in all_steps:
            tot = step.action_items.filter(is_deleted = False).all().count()
            tot_ai = tot_ai+tot
        return tot_ai

    class Meta:
        #ordering = ['module_priority',]
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'

    def __str__(self):
        return f"{self.title}"


class Steps(LogBaseModel):
    step_id = models.BigAutoField(primary_key=True)
    step_sno = models.IntegerField(blank=True, null=True, default=1)
    module = models.ForeignKey(
        Modules, on_delete=models.CASCADE, related_name="steps")
    title = models.CharField(max_length=500, blank=False, null=False)
    description = models.TextField(default='', blank=True)
    # total_action_items=models.IntegerField(blank=True,null=True)
    bg_image = models.FileField(upload_to='images', blank=True)
    frequency = models.CharField(max_length=10, blank=True, default='')
    step_completion_time= models.CharField(max_length=3, blank=True, default='')
    is_backup_step = models.BooleanField(default=False, null=True, blank=True)
    
    def link_to_step(self):
        link=reverse("admin:courses_steps_change", args=[self.step_id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')
    class Meta:
        ordering = ('step_sno',)
        verbose_name = 'Step'
        verbose_name_plural = 'Steps'

    def __str__(self):
        return f"{self.module} : {self.title}"


class ActionDataTypes(LogBaseModel):
    datatype = models.CharField(max_length=200, blank=False, null=False)

    class Meta:
        verbose_name = 'ActionDataType'
        verbose_name_plural = 'ActionDataTypes'

    def __str__(self):
        return f"{self.datatype}"


class ActionItems(LogBaseModel):
    action_id = models.BigAutoField(primary_key=True)
    action_sno = models.IntegerField(blank=True, null=True, default=1)
    step = models.ForeignKey(
        Steps, on_delete=models.CASCADE, related_name="action_items")
    title = models.CharField(max_length=500, blank=False, null=False)
    description = RichTextField(blank=True, null = True)
    action_type = models.ForeignKey(
        ActionDataTypes, on_delete=models.DO_NOTHING, related_name="action_type")
    actionItem_completion_time= models.CharField(max_length=3, blank=True, default='')
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item(self):
        link=reverse("admin:courses_actionitems_change", args=[self.action_id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')

    class Meta:
        ordering = ('action_sno',)
        verbose_name = 'ActionItem'
        verbose_name_plural = 'ActionItems'

    def __str__(self):
        return f"{self.title}"


class ActionFileTypes(LogBaseModel):
    filetype = models.CharField(max_length=200, blank=False, null=False)

    class Meta:
        verbose_name = 'ActionFileType'
        verbose_name_plural = 'ActionFileTypes'

    def __str__(self):
        return f"{self.filetype}"

class ActionItemTypeTable(LogBaseModel):
    action_item = models.ForeignKey(ActionItems, on_delete=models.CASCADE, related_name="actionitem_type_table")
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.CharField(max_length=500, blank=False, null=False)
    file_link = models.FileField(upload_to='files', blank=True)
    description = models.TextField(blank=True)
    questions = models.JSONField(default=dict)
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item_type_table(self):
        link=reverse("admin:courses_actionitemtypetable_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')
        
    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemTypeTable'
        verbose_name_plural = 'ActionItemTypeTables'

    def __str__(self):
        return f"{self.title}"

class ActionItemGoogleForm(LogBaseModel):
    action_item = models.ForeignKey(ActionItems, on_delete=models.CASCADE, related_name="actionitem_google_form")
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.CharField(max_length=500, blank=False, null=False)
    file_link = models.FileField(upload_to='files', blank=True)
    description = models.TextField(blank=True)
    question = models.CharField(max_length=1000, blank=True, null=True)
    type = models.CharField(max_length=200,default='Other', choices=CHOICES_GOOGLE_FORM, blank=True,  null=True)
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item_google_form(self):
        link=reverse("admin:courses_actionitemgoogleform_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')
        
    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemGoogleForm'
        verbose_name_plural = 'ActionItemGoogleForms'

    def __str__(self):
        return f"{self.title}"

from django.forms.widgets import Textarea

class NoSortJSONField(models.TextField):
    def formfield(self, **kwargs):
        # Use the custom widget for the JSON field
        kwargs['widget'] = Textarea(attrs={'rows': 10})
        return super().formfield(**kwargs)

class ActionItemFramework(LogBaseModel):
    action_item = models.ForeignKey(ActionItems, on_delete=models.CASCADE, related_name="actionitem_framework")
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.CharField(max_length=500, blank=False, null=False)
    description = models.TextField(blank=True)
    # questions = models.JSONField(default=dict)
    questions = NoSortJSONField()
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item_framework(self):
        link=reverse("admin:courses_actionitemframework_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')

    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemFramework'
        verbose_name_plural = 'ActionItemFrameworks'

    def __str__(self):
        return f"{self.title}"

CHOICE_OPTION_ACTIONITEM_RELATION_TYPE = [
    ('AutoFill', 'AutoFill'),
    ('Other', 'Other'),
]
class ActionItemConnectWithOtherActionItem(LogBaseModel):
    primary_action_item = models.ForeignKey(ActionItems, on_delete=models.CASCADE, related_name="primary_action_item")
    secondary_action_item = models.ForeignKey(ActionItems, on_delete=models.CASCADE, related_name="secondary_action_item")
    ai_relation_type = models.CharField(max_length=50, default="AutoFill", choices=CHOICE_OPTION_ACTIONITEM_RELATION_TYPE, blank=True,  null=True)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'ActionItemConnectWithOtherActionItem'
        verbose_name_plural = 'ActionItemConnectWithOtherActionItems'

    def __str__(self):
        return f"{self.primary_action_item}"

CHOICES_OPTION_GOOGLE_FORM_TYPE = [
    ('MCQ', 'MCQ'),
    ('Dropdown', 'Dropdown'),
]

class ActionItemGoogleFormOption(LogBaseModel):
    action_item_google_form = models.ForeignKey(ActionItemGoogleForm, on_delete=models.CASCADE, related_name="google_form_options")
    sno = models.IntegerField(blank=True, null=True, default=1)
    option = models.CharField(max_length=200, blank=False, null=False)
    option_type = models.CharField(max_length=50, default="MCQ", choices=CHOICES_OPTION_GOOGLE_FORM_TYPE, blank=True,  null=True)
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item_google_form_option(self):
        link=reverse("admin:courses_actionitemgoogleformoption_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')

    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemGoogleFormOption'
        verbose_name_plural = 'ActionItemGoogleFormOptions'

    def __str__(self):
        return f"{self.option}"

class ActionItemTypeTableStep8(LogBaseModel):
    action_item = models.ForeignKey(ActionItems, on_delete=models.CASCADE, related_name="actionitem_type_table_step8")
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.CharField(max_length=500, blank=False, null=False)
    description = models.TextField(blank=True)
    criteria_question_head = models.CharField(max_length=200, blank=True, null=True)
    criteria_question_text = models.CharField(max_length=200, blank=True, null=True)
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item_type_table_step8(self):
        link=reverse("admin:courses_actionitemtypetablestep8_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')
        
    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemTypeTableStep8'
        verbose_name_plural = 'ActionItemTypeTableStep8s'

    def __str__(self):
        return f"{self.title}"

class ActionItemFiles(LogBaseModel):
    action_item = models.ForeignKey(
        ActionItems, on_delete=models.CASCADE, related_name="files")
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.CharField(max_length=500, blank=False, null=False)
    file = models.FileField(upload_to='files')
    description = models.TextField(blank=True, null = True)
    file_box_heading = models.CharField(max_length=100, blank=True, null=True)
    file_box_text = models.CharField(max_length=500, blank=True, null=True)
    file_box_link = models.URLField(blank = True, null = True)
    file_question = models.CharField(max_length=500, blank=True, null=True)
    file_uploadbox_heading = models.CharField(max_length=100, blank=True, null=True)
    file_uploadbox_text = models.CharField(max_length=500, blank=True, null=True)
    filetype = models.ForeignKey(
        ActionFileTypes, on_delete=models.CASCADE, related_name="file_types", blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    
    def link_to_action_item_file(self):
        link=reverse("admin:courses_actionitemfiles_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')

    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemFile'
        verbose_name_plural = 'ActionItemFiles'

    def __str__(self):
        return f"{self.title}"


class ActionLinkTypes(LogBaseModel):
    linktype = models.CharField(max_length=200, blank=False, null=False)

    class Meta:
        verbose_name = 'ActionLinkType'
        verbose_name_plural = 'ActionLinkTypes'

    def __str__(self):
        return f"{self.linktype}"


class ActionItemLinks(LogBaseModel):
    action_item = models.ForeignKey(
        ActionItems, on_delete=models.CASCADE, related_name="links")
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.CharField(max_length=500, blank=False, null=False)
    link = models.URLField()
    description = models.TextField(blank=True)
    linktype = models.ForeignKey(
        ActionLinkTypes, on_delete=models.CASCADE, related_name="link_types", blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    
    def link_to_action_item_link(self):
        link=reverse("admin:courses_actionitemlinks_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.title}</a>')
    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemLink'
        verbose_name_plural = 'ActionItemLinks'

    def __str__(self):
        return f"{self.title}"


class ActionItemDiary(LogBaseModel):
    action_item = models.ForeignKey(
        ActionItems, on_delete=models.CASCADE, related_name="diary")
    sno = models.IntegerField(blank=True, null=True, default=1)
    question = models.CharField(max_length=1000, blank=False, null=False)
    is_deleted = models.BooleanField(default=False)
    is_linked_with_ai_comment = models.BooleanField(default=False)
    
    def link_to_action_item_diary(self):
        link=reverse("admin:courses_actionitemdiary_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')

    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemDiary'
        verbose_name_plural = 'ActionItemDiary'

    def __str__(self):
        return f"{self.question}"

class ActionItemExitTicket(LogBaseModel):
    action_item = models.ForeignKey(
        ActionItems, on_delete=models.CASCADE, related_name="exit_tickets")
    sno = models.IntegerField(blank=True, null=True, default=1)
    question = models.CharField(max_length=1000, blank=False, null=False)
    sub_title_question = models.CharField(max_length=1000, blank=True, null=True)
    type = models.CharField(max_length=200,default='Other', choices=CHOICE_EXIT_TICKET_TYPE, blank=True,  null=True)
    is_deleted = models.BooleanField(default=False)

    def link_to_action_item_exit_ticket(self):
        link=reverse("admin:courses_actionitemexitticket_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')

    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemExitTicket'
        verbose_name_plural = 'ActionItemExitTickets'

    def __str__(self):
        return f"{self.question}"


class ActionItemExitTicketOptions(LogBaseModel):
    action_item_exit_ticket = models.ForeignKey(
        ActionItemExitTicket, on_delete=models.CASCADE, related_name="exit_ticket_options")
    sno = models.IntegerField(blank=True, null=True, default=1)
    option = models.CharField(max_length=200, blank=False, null=False)
    is_deleted = models.BooleanField(default=False)

    class Meta:
        ordering = ('sno',)
        verbose_name = 'ActionItemExitTicketOption'
        verbose_name_plural = 'ActionItemExitTicketOptions'

    def __str__(self):
        return f"{self.option}"

class ScholarshipTest(LogBaseModel):
    title = models.CharField(max_length=500,blank=True, null=True)
    is_active = models.BooleanField(default=False, null=True)
    lang_code = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'ScholarshipTest'
        verbose_name_plural = 'ScholarshipTests'

QUESTION_TYPE = [
    ("Text", "Text"),
    ("MCQ", "MCQ")
]

class ScholarshipTestQuestion(LogBaseModel):
    scholarship_test = models.ForeignKey(ScholarshipTest, on_delete=models.CASCADE, related_name="scholarship_test_questions", default='')
    sno = models.IntegerField(blank=True, null=True, default=1)
    question = models.CharField(max_length=250, blank=True, null=True)
    lang_code = models.CharField(max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    question_type = models.CharField(max_length=20, default="Text", choices=QUESTION_TYPE)

    def __str__(self):
        return f"{self.question}-{self.sno}"
    
    class Meta:
        verbose_name = "ScholarshipTestQuestion"
        verbose_name_plural = "ScholarshipTestQuestions"

CHOISE_PERSONALITY_TEST_CATEGORIES = [
    ("Realistic", "Realistic"),
    ("Investigative", "Investigative"),
    ("Artistic", "Artistic"),
    ("Social", "Social"),
    ("Enterprising", "Enterprising"),
    ("Conventional", "Conventional"),
]

CHOISE_OPTIONS = [
    ("Agree", _("Agree")),
    ("Disagree", _("Disagree")),
]

class PersonalityTest(LogBaseModel):
    title = models.CharField(max_length=500,blank=True, null=True)
    is_active = models.BooleanField(default=False, null=True)
    lang_code = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'PersonalityTest'
        verbose_name_plural = 'PersonalityTests'

class PersonalityTestQuestion(LogBaseModel):
    personality_test = models.ForeignKey(PersonalityTest, on_delete=models.CASCADE, related_name="personalitytestquestions")
    sno = models.IntegerField(blank=True, null=True, default=1)
    question = models.CharField(max_length=500, null=True, blank=True)
    category = models.CharField(max_length=50, null=True, blank=True, choices=CHOISE_PERSONALITY_TEST_CATEGORIES)

    class Meta:
        verbose_name = 'PersonalityTestQuestion'
        verbose_name_plural = 'PersonalityTestQuestions'

    def __str__(self):
        return f"<Question : {self.question} >"

class PTQuestionOption(LogBaseModel):
    personality_test_question = models.ForeignKey(PersonalityTestQuestion, on_delete=models.CASCADE, related_name="ptquestionoptions")
    sno = models.IntegerField(blank=True, null=True, default=1)
    option = models.CharField(max_length=50, null=True, blank=True, choices=CHOISE_OPTIONS)

    class Meta:
        verbose_name = 'PTQuestionOption'
        verbose_name_plural = 'PTQuestionOptions'


CHOICE_IS_Active = [
    ("Yes", "Yes"),
    ("No", "No")
]

CHOICES_COHORT_TYPE = (
    ("Paid","Paid"),
    ("Trial","Trial"),
    ("Test","Test"),
)

class CohortManager(models.Manager):
    def lang_code(self, lang):
        return super(CohortManager, self).get_queryset().filter(cohort_lang=lang)


class Cohort(LogBaseModel):
    cohort_id = models.BigAutoField(primary_key=True)
    # course=models.ForeignKey(Courses,on_delete=models.CASCADE,related_name="cohort_course")
    module = models.ForeignKey(
        Modules, on_delete=models.CASCADE, related_name="cohort_module")
    cohort_name = models.CharField(max_length=200, blank=True, default='')
    starting_date = models.DateField(blank=True, null=True)
    price = models.CharField(max_length=10, default='', blank=True)
    duration = models.CharField(max_length=10, default='', blank=True)
    is_active = models.CharField(
        max_length=3, default='No', blank=True, choices=CHOICE_IS_Active)
    cohort_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    cohort_type = models.CharField(max_length=20,default="Paid",blank=True,null=True,choices=CHOICES_COHORT_TYPE)
    objects = models.Manager()  # The default manager.
    cohortManager = CohortManager()  # Our custom manager.
    is_for_middle_school = models.BooleanField(default=False, blank=True, null= True)
    is_for_fast_track_program = models.BooleanField(default=False, blank=True, null= True)

    def link_to_cohort(self):
        link=reverse("admin:courses_cohort_change", args=[self.cohort_id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>') 

    @property
    def is_available_to_purchase(self):
        dt = datetime.date.today()
        if (dt > self.starting_date):
            return False
        else:
            return True

    @property
    def tot_students(self):
        return self.cohortMapID.all().count()

    @property
    def tot_steps(self):
        tot = self.cohort_step_status.all().count()
        return tot
    
    def is_cohort_step3_locked(self):
        step_3 = self.cohort_step_status.filter(step__step_sno=3).first()
        if step_3.is_active:
            return False
        else:
            return True

    @property
    def tot_action_items(self):
        tot_ai = 0
        all_steps = self.cohort_step_status.all()
        for step in all_steps:
            tot = step.step.action_items.filter(is_deleted = False).all().count()
            tot_ai = tot_ai+tot
        return tot_ai

    class Meta:
        verbose_name = 'Cohort'
        verbose_name_plural = 'Cohort'

    def __str__(self):
        return f"{self.cohort_name}"


class step_status(LogBaseModel):
    cohort = models.ForeignKey(
        Cohort, on_delete=models.CASCADE, related_name="cohort_step_status")
    step = models.ForeignKey(
        Steps, on_delete=models.CASCADE, related_name="step_name")
    # duration=models.CharField(max_length=10,default='',blank=True)
    starting_date = models.DateField(blank=True, null=True)
    # is_active=models.CharField(max_length=3,default='No',blank=True,choices=CHOICE_IS_Active)

    def link_to_step_status(self):
        link=reverse("admin:courses_step_status_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>') 

    @property
    def is_active(self):
        dt = datetime.date.today()
        if (dt >= self.starting_date):
            return True
        else:
            return False

    def is_active_one_week_ago(self):
        dt = datetime.date.today() - timedelta(days=7)
        if (dt >= self.starting_date):
            return True
        else:
            return False
        
    @property
    def is_active_2weeks_ago(self):
        dt = datetime.date.today() - timedelta(days=14)
        if (dt >= self.starting_date):
            return True
        else:
            return False

    @property
    def tot_action_items(self):
        tot = self.step.action_items.filter(is_deleted=False).exclude(action_type__datatype="Exit").all().count()
        return tot

    class Meta:
        ordering = ['step__step_sno']
        verbose_name = 'step_status'
        verbose_name_plural = 'step_status'

    def __str__(self):
        return f"{self.step}:{self.starting_date}"


STATUS_CHOICES = (
    ('draft', 'Draft'),
    ('published', 'Published'),
)


class PublishedManager(models.Manager):
    def get_queryset(self):
        return super(PublishedManager, self).get_queryset().filter(status='published')

    def lang_code(self, lang):
        return super(PublishedManager, self).get_queryset().filter(module_lang=lang, status='published')


class Blog_post(LogBaseModel):
    title = models.CharField(max_length=250)
    slug = models.SlugField(
        max_length=250, unique_for_date='publish', blank=True, null=True)
    author = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name='blog_posts')
    body = models.TextField(blank=True, null=True)
    blog_link = models.URLField(blank=True, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    icon = models.FileField(upload_to='images', blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    objects = models.Manager()  # The default manager.
    published = PublishedManager()  # Our custom manager.

    class Meta:
        ordering = ('-publish_date',)
        verbose_name = 'Blog_post'
        verbose_name_plural = 'Blog_posts'

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('post_detail', args=[self.publish_date.year, self.publish_date.month, self.publish_date.day, self.slug])

WEBINAR_QUESTION_TYPE = [
    ("Pre", _("Pre")),
    ("Post", _("Post")),
]

def hubspot_properties_dict():
    return {
        "Reserve_seat_status": "hubspot_webinar_feb08_is_seat_reserved",
        "Attendance_status": "hubspot_webinar_feb08_is_attendance_marked",
    }


class Webinars(LogBaseModel):
    title = models.CharField(max_length=250)
    author = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name='webinars')
    description = models.TextField(null=True, blank=True)
    link = models.URLField(blank=True, null=True)
    webinar_start_date = models.DateTimeField(default=timezone.now)
    reservation_start_date = models.DateTimeField(default=timezone.now)
    datetime_to_mark_attendance = models.DateTimeField(default=timezone.now)
    icon = models.FileField(upload_to='images', blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    maximum_seats = models.IntegerField(default=100,blank=True, null=True)
    allocated_seats = models.IntegerField(default=0,blank=True, null=True)
    pcto_hours = models.IntegerField(default=1,blank=True, null=True)
    attendance_code = models.CharField(max_length=20, blank=True, null=True)
    webinar_accessibility = models.ManyToManyField(OurPlans)
    # webinar_accessibility = models.ForeignKey(OurPlans, on_delete=models.DO_NOTHING, related_name="webinars",blank=True, null=True)
    objects = models.Manager()  # The default manager.
    published = PublishedManager()  # Our custom manager.
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    hubspot_properties = models.JSONField(default=hubspot_properties_dict)

    @property
    def number_of_seats_left(self):
        seats = self.maximum_seats - self.allocated_seats
        return seats
        
    @property
    def is_seat_vacant(self):
        return self.maximum_seats > self.allocated_seats

    @property
    def is_past_due(self):
        return date.today() > self.webinar_start_date

    @property
    def is_reservation_started(self):
        local_tz = pytz.timezone(settings.TIME_ZONE)
        current_date = local_tz.localize(datetime.datetime.now())
        # current_date = datetime.datetime.strftime(dt, "%d/%m/%Y %H:%M:%S")
        # reservation_start_date = datetime.datetime.strftime(self.reservation_start_date, "%d/%m/%Y %H:%M:%S")
        sts = current_date >= self.reservation_start_date
        return sts

    @property
    def is_mark_attendance_statred(self):
        local_tz = pytz.timezone(settings.TIME_ZONE)
        current_date = local_tz.localize(datetime.datetime.now())
        # current_date = datetime.datetime.strftime(dt, "%d/%m/%Y %H:%M:%S")
        # datetime_to_mark_attendance = datetime.datetime.strftime(self.datetime_to_mark_attendance, "%d/%m/%Y %H:%M:%S")
        # webinar_start_date = datetime.datetime.strftime(self.webinar_start_date, "%d/%m/%Y %H:%M:%S")
        if current_date >= self.webinar_start_date:
            return self.datetime_to_mark_attendance >= current_date
        else:
            return False

    @property
    def is_webinar_start_date(self):
        local_tz = pytz.timezone(settings.TIME_ZONE)
        current_date = local_tz.localize(datetime.datetime.now())
        # current_date = datetime.datetime.strftime(dt, "%d/%m/%Y %H:%M:%S")
        # webinar_start_date = datetime.datetime.strftime(self.webinar_start_date, "%d/%m/%Y %H:%M:%S")
        if current_date <= self.webinar_start_date:
            return True
        else:
            return False

    class Meta:
        ordering = ('webinar_start_date',)
        verbose_name = 'Webinars'
        verbose_name_plural = 'Webinars'

    def __str__(self):
        return self.title


class WebinarQuestionnaire(LogBaseModel):
    title = models.CharField(max_length=500,blank=True, null=True)
    is_active = models.BooleanField(default=False, null=True)
    test_type = models.CharField(max_length=20, choices=WEBINAR_QUESTION_TYPE)
    lang_code = models.CharField(max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    webinar = models.ManyToManyField(Webinars) #null=True, blank=True, on_delete=models.CASCADE

    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = 'WebinarQuestionnaire'
        verbose_name_plural = 'WebinarQuestionnaires'

class WebinarQuestion(LogBaseModel):
    question = models.CharField(max_length=500, null=True, blank=True)
    webinar_test = models.ForeignKey(WebinarQuestionnaire, on_delete=models.CASCADE, related_name="webinar_test_question")

    class Meta:
        verbose_name = 'WebinarQuestion'
        verbose_name_plural = 'WebinarQuestions'


class Notification_type(LogBaseModel):
    notification_type = models.CharField(max_length=15)
    description = models.CharField(
        max_length=200, blank=False, null=False, default="")

    class Meta:
        verbose_name = 'Notification_type'
        verbose_name_plural = 'Notification_types'

    def __str__(self):
        return self.notification_type


class Notification(LogBaseModel):
    cohort = models.ForeignKey(
        Cohort, on_delete=models.CASCADE, related_name="notifications",blank=True,null=True)
    student = models.ForeignKey(
        authMdl.Person, on_delete=models.CASCADE, related_name="stu_notifications",blank=True,null=True)
    title = models.CharField(max_length=100)
    notification_type = models.ForeignKey(
        Notification_type, on_delete=models.CASCADE, related_name="notifications")

    class Meta:
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return self.title


GROUP_TYPE = (
    ('whatsapp', 'Whatsapp'),
    ('facebook', 'Facebook'),
)


class MyGroups(LogBaseModel):
    cohort = models.ForeignKey(
        Cohort, on_delete=models.CASCADE, related_name="mygroups")
    group_title = models.CharField(max_length=70)
    group_link = models.URLField()
    group_type = models.CharField(
        max_length=20, choices=GROUP_TYPE, default='whatsapp')

    class Meta:
        verbose_name = 'MyGroup'
        verbose_name_plural = 'MyGroups'

    def __str__(self):
        return self.group_title


class MyResources(LogBaseModel):
    resource_title = models.CharField(max_length=70)
    resource_description = models.TextField(blank=True, default='')
    resource_link = models.URLField()
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    objects = models.Manager()  # The default manager.
    resourceManager = ModuleManager()  # Our custom manager

    class Meta:
        verbose_name = 'MyResource'
        verbose_name_plural = 'MyResources'

    def __str__(self):
        return self.resource_title


class MyVideos(LogBaseModel):
    video_title = models.CharField(max_length=70)
    video_link = models.URLField()
    video_description = models.TextField(blank=True, default='')
    front_pic = models.FileField(upload_to='images', blank=True)
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    objects = models.Manager()  # The default manager.
    videoManager = ModuleManager()  # Our custom manager

    class Meta:
        verbose_name = 'MyVideo'
        verbose_name_plural = 'MyVideos'

    def __str__(self):
        return self.video_title

class WelcomeVideo(LogBaseModel):
    video_title = models.CharField(max_length=70,blank=True)
    video_link = models.URLField()
    video_description = models.TextField(blank=True, default='')
    front_pic = models.FileField(upload_to='images', blank=True)
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    is_published = models.BooleanField(default=False)
    objects = models.Manager()  # The default manager.
    videoManager = ModuleManager()  # Our custom manager

    class Meta:
        verbose_name = 'WelcomeVideo'
        verbose_name_plural = 'WelcomeVideos'

    def __str__(self):
        return self.video_title

class MyPdfs(LogBaseModel):
    pdf_title = models.CharField(max_length=70,blank=True)
    pdf_file = models.FileField(upload_to='files')
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    is_published = models.BooleanField(default=False)
    is_for_middle_school = models.BooleanField(default=False, blank=True, null= True)

    objects = models.Manager()  # The default manager.

    class Meta:
        verbose_name = 'MyPdf'
        verbose_name_plural = 'MyPdfs'

    def __str__(self):
        return self.pdf_title

CHOICE_BlogVideo = (
    ('blogs', 'Blogs'),
    ('videos', 'Videos'),
)


class MyBlogVideos(LogBaseModel):
    sno = models.IntegerField(null=True, blank=True)
    title = models.CharField(max_length=250)
    description = models.TextField(blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    publish_date = models.DateTimeField(default=timezone.now)
    icon = models.FileField(upload_to='images', blank=True)
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default='draft')
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)
    type = models.CharField(
        max_length=20, default="blogs", blank=True, choices=CHOICE_BlogVideo)
    is_for_fast_track = models.BooleanField(default=False, blank=True, null= True)
    duration = models.CharField(max_length=20, blank=True, null=True)
    objects = models.Manager()  # The default manager.
    published = PublishedManager()  # Our custom manager.

    class Meta:
        ordering = ('-publish_date',)
        verbose_name = 'MyBlogVideo'
        verbose_name_plural = 'MyBlogVideos'

    def __str__(self):
        return self.title

DAY_OF_THE_WEEK = (
    ('0' , 'Monday'),
    ('1' , 'Tuesday'),
    ('2' , 'Wednesday'),
    ('3' , 'Thursday'),
    ('4' , 'Friday'),
    ('5' , 'Saturday'), 
    ('6' , 'Sunday'),
)

CHOICES_MEET_APP = (
    ('Zoom','Zoom'),
)

class MeetupCommunity(LogBaseModel):
    title = models.CharField(max_length=100)
    meet_link = models.URLField()
    meet_week_number = models.IntegerField(blank=True, null=True, default=3)
    meet_day=models.CharField(max_length=100,choices=DAY_OF_THE_WEEK)
    meet_time = models.TimeField(default=timezone.now)
    meet_tutor_name = models.CharField(max_length=100)
    is_Active = models.BooleanField(default=False)
    meet_app = models.CharField(max_length=20,choices=CHOICES_MEET_APP,default='Zoom')
    meetup_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_Lang)

    class Meta:
        verbose_name = 'MeetupCommunity'
        verbose_name_plural = 'MeetupCommunity'

    def __str__(self):
        return self.title

class Meetup(LogBaseModel):
    cohort = models.ForeignKey(Cohort, on_delete=models.CASCADE, related_name="meetups")
    step_status = models.ForeignKey(step_status, on_delete=models.CASCADE,related_name="meetups")
    title = models.CharField(max_length=100)
    meet_link = models.URLField()
    meet_date_time = models.DateTimeField(default=timezone.now)
    meet_tutor_name = models.CharField(max_length=100)
    is_Active = models.BooleanField(default=False)
    meet_app = models.CharField(max_length=20,choices=CHOICES_MEET_APP,default='Zoom')

    class Meta:
        ordering = ('meet_date_time',)
        verbose_name = 'Meetup'
        verbose_name_plural = 'Meetups'

    def __str__(self):
        return self.title

class PushNotificationTopics(LogBaseModel):
    topic_name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'PushNotificationTopic'
        verbose_name_plural = 'PushNotificationTopics'
    def __str__(self):
        return self.topic_name

class PushNotificationRecords(LogBaseModel):
    topic = models.ForeignKey(PushNotificationTopics, on_delete=models.CASCADE)
    title = models.CharField(max_length=100, blank=True, default='')
    body = models.TextField(default='', blank=True)
    response_msg_id = models.CharField(max_length=100, blank=True, default='')
    
    class Meta:
        verbose_name = 'PushNotificationRecord'
        verbose_name_plural = 'PushNotificationRecords'
    def __str__(self):
        return self.title

class CohortPushNotificationRecords(LogBaseModel):
    topic = models.CharField(max_length=100, blank=True, default='')
    title = models.CharField(max_length=100, blank=True, default='')
    body = models.TextField(default='', blank=True)
    response_msg_id = models.CharField(max_length=100, blank=True, default='')
    
    class Meta:
        verbose_name = 'CohortPushNotificationRecord'
        verbose_name_plural = 'CohortPushNotificationRecords'
    def __str__(self):
        return self.title

class TestCohortID(LogBaseModel):
    cohort = models.ForeignKey(Cohort,on_delete=models.CASCADE, related_name="test_cohort_id")

    class Meta:
        verbose_name = 'TestCohortID'
        verbose_name_plural = 'TestCohortIDs'

class JobPosting(LogBaseModel):
    title = models.CharField(max_length=255,null=False, blank=False)
    company_name = models.CharField(max_length=255,null=False, blank=False)
    company_to_display_specific_jobs = models.ForeignKey(authMdl.Company,on_delete=models.CASCADE, null=True, blank=True)
    company_logo = models.ImageField(upload_to='company_logos/',null=False, blank=False)
    location = models.CharField(max_length=255,null=False, blank=False)
    job_portal_link = models.URLField(null=False, blank=False)
    start_date = models.DateField(auto_now_add=True)
    job_date = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=False)
    
    class Meta:
        verbose_name = 'JobPosting'
        verbose_name_plural = 'JobPostings'
        

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        notify_students_about_job_posting.delay()

