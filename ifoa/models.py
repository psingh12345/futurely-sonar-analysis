from django.db import models
from userauth.models import TimeStampModel
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
from ckeditor.fields import RichTextField

CHOICES_GENDER = [
    # ("Gender", _("Gender")),
    ("Male", _("Male")),
    ("Female", _("Female")),
    ("Other", _("Other"))
]

CHOICES_ASSESSMENT_STATUS  = [
    ("Completed", _("Completed")),
    ("Started", _("Started")),
    ("Pending", _("Pending")),
]

CHOICES_HOW_KNOW_US = [
    ("Select", "Select"),
    ("Facebook", "Facebook"),
    ("Instagram", "Instagram"),
    ("Tik Tok", "Tik Tok"),
    ("Google", "Google"),
    ("Friends", _("Friends")),
    ("Parents", _("Parents")),
    ("School", _("School")),
    ("Radio", "Radio"),
    ("News Paper", _("News Paper")),
    ("Linkedin", "Linkedin"),
    ("Sito IFOA", "Sito IFOA"),
    ("Other", _("Other")),
]

class IFOAStudentDetail(TimeStampModel):
    session_id = models.CharField(max_length=200)
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    gender = models.CharField(max_length=10, choices=CHOICES_GENDER, blank=True, null=True, default="")
    date_of_birth = models.DateField(blank=False)
    birth_place = models.CharField(max_length=100, blank=False)
    tax_id_code = models.CharField(max_length=100, blank=False)
    phone_number = models.CharField(max_length=100, blank=False)
    email = models.EmailField(max_length=100)
    how_did_you_know_us = models.CharField(max_length=50, blank=True, null=True, choices=CHOICES_HOW_KNOW_US, default="")
    assessment_status = models.CharField(max_length=20, blank=True, null=True, choices=CHOICES_ASSESSMENT_STATUS)
    certificate_link = models.FileField(upload_to='', blank=True, null=True)
    clarity_token = models.CharField(max_length=100, blank=True, null=True)
    is_otp_verified = models.BooleanField(default=False)
    finalità_di_marketing = models.CharField(max_length=100, blank=True, null=True, default="Yes")
    informativa_sulla_privacy = models.CharField(max_length=100, blank=True, null=True, default="Yes")


    class Meta:
        verbose_name = 'IFOAStudentDetail'
        verbose_name_plural = 'IFOAStudentDetail'

    def __str__(self):
        return f"{self.email}"

CHOICES_TEST_TYPE = [
    ('IFOA', 'IFOA'),
    ('Other', 'Other'),
]
    
class IFOATest(TimeStampModel):
    test_title = models.CharField(max_length=50, blank=False)
    type = models.CharField(max_length=20, choices=CHOICES_TEST_TYPE, default="IFOA")

    class Meta:
        verbose_name = 'IFOATest'
        verbose_name_plural = 'IFOATest'

    def __str__(self):
        return f"{self.test_title}"
    

CHOICES_QUESTION_TYPE = [
    ('MCQ', 'MCQ'),
    ('Text', 'Text'),
]
CHOISE_PERSONALITY_TEST_CATEGORIES = [
    ("Realistic", "Realistic"),
    ("Investigative", "Investigative"),
    ("Artistic", "Artistic"),
    ("Social", "Social"),
    ("Enterprising", "Enterprising"),
    ("Conventional", "Conventional"),
]

class IFOAPTQuestion(TimeStampModel):
    ifoa_test = models.ForeignKey(IFOATest, on_delete=models.CASCADE, related_name="ifoa_test_question")
    question = models.CharField(max_length=200, blank=False)
    question_type = models.CharField(max_length=30, choices=CHOICES_QUESTION_TYPE, default="MCQ")
    question_category = models.CharField(max_length=30, choices=CHOISE_PERSONALITY_TEST_CATEGORIES, default="Realistic")

    class Meta:
        verbose_name = 'IFOAPTQuestion'
        verbose_name_plural = 'IFOAPTQuestions'

    def __str__(self):
        return f"{self.question}"


class IFOAPTQuestionMCQOption(TimeStampModel):
    ifoa_question = models.ForeignKey(IFOAPTQuestion, on_delete=models.CASCADE, related_name="ifoa_qus_option")
    option = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = 'IFOAPTQuestionMCQOption'
        verbose_name_plural = 'IFOAPTQuestionMCQOptions'

    def __str__(self):
        return f"{self.option}"
    
CHOICES_NEXT_QUESTION_TYPE = [
    ("MCQ", "MCQ"),
    ("Link", "Link"),
    ('Text', 'Text'),
]


class IFOAQuestion(TimeStampModel):
    sno = models.IntegerField(default=1)
    ifoa_test = models.ForeignKey(IFOATest, on_delete=models.CASCADE, related_name="ifoa_question")
    # question = models.CharField(max_length=200, blank=False)
    question = RichTextField(blank=True, null = True)
    question_type = models.CharField(max_length=30, choices=CHOICES_NEXT_QUESTION_TYPE, default="MCQ")

    class Meta:
        verbose_name = 'IFOAQuestion'
        verbose_name_plural = 'IFOAQuestions'
        # ordering = ['sno']

    def __str__(self):
        return f"{self.question} - {self.sno}"
    

class IFOAQuestionLink(TimeStampModel):
    ifoa_question = models.ForeignKey(IFOAQuestion, on_delete=models.CASCADE, related_name="ifoa_question_link")
    link = models.CharField(max_length=200, blank=False, null=False)

    class Meta:
        verbose_name = 'IFOAQuestionLink'
        verbose_name_plural = 'IFOAQuestionLinks'

    def __str__(self):
        return f"{self.link}"
    

class IFOAQuestionMCQOption(TimeStampModel):
    ifoa_question = models.ForeignKey(IFOAQuestion, on_delete=models.CASCADE, related_name="ifoa_question_option")
    option = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = 'IFOAQuestionMCQOption'
        verbose_name_plural = 'IFOAQuestionMCQOptions'

    def __str__(self):
        return f"{self.option}"

class IFOAQuestionMCQOptionLinkedQuestion(TimeStampModel):
    ifoa_question_mcq_option = models.ForeignKey(IFOAQuestionMCQOption, on_delete=models.CASCADE, related_name="ifoa_question_option_linked", null=True, blank=True)
    ifoa_question = models.ForeignKey(IFOAQuestion, on_delete=models.CASCADE, related_name="ifoa_question_linked")

    class Meta:
        verbose_name = 'IFOAQuestionMCQOptionLinkedQuestion'
        verbose_name_plural = 'IFOAQuestionMCQOptionLinkedQuestions'
    
class IFOAQuestionOptionLink(TimeStampModel):
    ifoa_question_option = models.ForeignKey(IFOAQuestionMCQOption, on_delete=models.CASCADE, related_name="ifoa_question_option_link")
    video_link = models.CharField(max_length=200, blank=False, null=False)

    class Meta:
        verbose_name = 'IFOAQuestionOptionLink'
        verbose_name_plural = 'IFOAQuestionOptionLinks'

    def __str__(self):
        return f"{self.video_link}"
    

class IFOAStudentPTMapper(TimeStampModel):
    ifoa_student_detail = models.ForeignKey(IFOAStudentDetail, on_delete=models.CASCADE, related_name="ifoa_student_detail")
    ifoa_test = models.ForeignKey(IFOATest, on_delete=models.CASCADE, related_name="ifoa_test")
    test_result = models.CharField(max_length=50, null=True, blank=True)
    is_completed = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = 'IFOAStudentPTMapper'
        verbose_name_plural = 'IFOAStudentPTMappers'

    def __str__(self):
        return f"{self.ifoa_student_detail} > {self.ifoa_test}"

    @property
    def calculate_my_score(self):
        result = {}
        result[("R","Realistic")] = self.ifoa_student_mapper.filter(answer="Agree",ifoa_question__question_category="Realistic").count()
        result[("I","Investigative")] = self.ifoa_student_mapper.filter(answer="Agree",ifoa_question__question_category="Investigative").count()
        result[("A","Artistic")] = self.ifoa_student_mapper.filter(answer="Agree",ifoa_question__question_category="Artistic").count()
        result[("S","Social")] = self.ifoa_student_mapper.filter(answer="Agree",ifoa_question__question_category="Social").count()
        result[("E","Enterprising")] = self.ifoa_student_mapper.filter(answer="Agree",ifoa_question__question_category="Enterprising").count()
        result[("C","Conventional")] = self.ifoa_student_mapper.filter(answer="Agree",ifoa_question__question_category="Conventional").count()
        return result


class IFOAStudentQuestionTracker(TimeStampModel):
    ifoa_student_detail = models.ForeignKey(IFOAStudentDetail, on_delete=models.CASCADE, related_name="student_detail_question_mapper", blank=True, null=True)
    ifoa_question = models.ForeignKey(IFOAQuestion, on_delete=models.CASCADE, related_name="ifoa_question_tracker")
    answer = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'IFOAStudentQuestionTracker'
        verbose_name_plural = 'IFOAStudentQuestionTrackers'


class IFOAStudentPTAnswer(TimeStampModel):
    ifoa_student_mapper = models.ForeignKey(IFOAStudentPTMapper, on_delete=models.CASCADE, related_name="ifoa_student_mapper")
    ifoa_question = models.ForeignKey(IFOAPTQuestion, on_delete=models.CASCADE, related_name="stu_ifoa_question", blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'IFOAStudentPTAnswer'
        verbose_name_plural = 'IFOAStudentPTAnswers'

    def __str__(self):
        return f"{self.ifoa_question}"