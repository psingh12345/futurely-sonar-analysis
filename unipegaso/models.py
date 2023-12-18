from django.db import models
from userauth.models import TimeStampModel
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html

CHOICES_GENDER = [
    ("Male", _("Male")),
    ("Female", _("Female")),
    ("Other", _("Other"))
]

CHOICES_ASSESSMENT_STATUS  = [
    ("Completed", _("Completed")),
    ("Started", _("Started")),
    ("Pending", _("Pending")),
]
CHOICES_COLLEGE = [
    ("Università telematica Pegaso", "Università telematica Pegaso"),
    ("Università telematica San Raffaele", "Università telematica San Raffaele"),
    ("Università Mercatorum", "Università Mercatorum"),
]

CHOICE_OPTION_TYPE = [
    ("UniPegaso", "UniPegaso"),
    ("Mercatorum", "Mercatorum"),
    ("Other", "Other"),
]

class ApprovedCentreOption(TimeStampModel):
    option = models.CharField(max_length=100, null=False, blank=False)
    option_type =  models.CharField(max_length=100, choices=CHOICE_OPTION_TYPE, default="UniPegaso")

    class Meta:
        verbose_name = '1_ApprovedCentreOption'
        verbose_name_plural = '1_ApprovedCentreOptions'

    def __str__(self):
        return f"{self.option}"

class StudentDetail(TimeStampModel):
    session_id = models.CharField(max_length=200) #unique=True)
    email = models.EmailField(max_length=100)
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    phone_number = models.CharField(max_length=100, blank=False)
    college = models.CharField(max_length=100, choices=CHOICES_COLLEGE, blank=True, null=True)
    year_of_enrollment = models.CharField(max_length=100, blank=False) #Date 
    are_you_taking_this_test_at_a_contracted_center = models.BooleanField(default=False)
    test_at_a_contracted_center_other = models.CharField(max_length=100, blank=True, null=True)
    assessment_status = models.CharField(max_length=20, blank=True, null=True, choices=CHOICES_ASSESSMENT_STATUS)
    certificate_link = models.FileField(upload_to='', blank=True, null=True)
    clarity_token = models.CharField(max_length=100, blank=True, null=True)


    class Meta:
        verbose_name = '9.0_StudentDetail'
        verbose_name_plural = '9.0_StudentDetails'

    def __str__(self):
        return f"{self.email}"

CHOICES_TEST_TYPE = [
    ('PT', 'PT'),
    ("UniMercatorum", "UniMercatorum"),
    ("UTSanRaffaele", "UTSanRaffaele"),
    ('Other', 'Other')
]

class UnipegasoTest(TimeStampModel):
    action_item_name = models.CharField(max_length=50, blank=False)
    type = models.CharField(max_length=20, choices=CHOICES_TEST_TYPE, default="PT")

    class Meta:
        verbose_name = '2_UnipegasoTest'
        verbose_name_plural = '2_UnipegasoTests'

    def __str__(self):
        return f"{self.action_item_name}"

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
class UniPegasoActionItemsPTQuestion(TimeStampModel):
    unipegaso_test = models.ForeignKey(UnipegasoTest, on_delete=models.CASCADE, related_name="unipegaso_test_question")
    question = models.CharField(max_length=200, blank=False)
    question_type = models.CharField(max_length=30, choices=CHOICES_QUESTION_TYPE, default="MCQ")
    question_category = models.CharField(max_length=30, choices=CHOISE_PERSONALITY_TEST_CATEGORIES, default="Realistic")

    class Meta:
        verbose_name = '3_UniPegasoActionItemsPTQuestion'
        verbose_name_plural = '3_UniPegasoActionItemsPTQuestions'

    def __str__(self):
        return f"{self.question}"
    
    def link_to_pt_question(self):
        link=reverse("admin:unipegaso_unipegasoactionitemsptquestion_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>') 

class UniPegasoActionItemPTOption(TimeStampModel):
    unipegaso_question = models.ForeignKey(UniPegasoActionItemsPTQuestion, on_delete=models.CASCADE, related_name="unipegaso_qus_option")
    option = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = '4_UniPegasoActionItemPTOption'
        verbose_name_plural = '4_UniPegasoActionItemPTOptions'

    def __str__(self):
        return f"{self.option}"

CHOICES_NEXT_QUESTION_TYPE = [
    ("MCQ", "MCQ"),
    ("Link", "Link"),
    ('Text', 'Text'),
]

class UnipegasoActionItemsNextQuestion(TimeStampModel):
    sno = models.IntegerField(default=1)
    unipegaso_test = models.ForeignKey(UnipegasoTest, on_delete=models.CASCADE, related_name="unipegaso_test")
    question = models.CharField(max_length=200, blank=False)
    question_type = models.CharField(max_length=30, choices=CHOICES_NEXT_QUESTION_TYPE, default="MCQ")

    class Meta:
        verbose_name = '5_UnipegasoActionItemsNextQuestion'
        verbose_name_plural = '5_UnipegasoActionItemsNextQuestions'

    def __str__(self):
        return f"{self.question} - {self.sno}"

    def link_to_next_question(self):
        link=reverse("admin:unipegaso_unipegasoactionitemsnextquestion_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>') 

class UnipegasoActionItemsNextQuestionOption(TimeStampModel):
    unipegaso_next_question = models.ForeignKey(UnipegasoActionItemsNextQuestion, on_delete=models.CASCADE, related_name="unipegaso_next_option")
    option = models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = '6_UnipegasoActionItemsNextQuestionOption'
        verbose_name_plural = '6_UnipegasoActionItemsNextQuestionOptions'

    def __str__(self):
        return f"{self.option}"

class UnipegasoVideoOptionLink(TimeStampModel):
    unipegaso_option = models.ForeignKey(UnipegasoActionItemsNextQuestionOption, on_delete=models.CASCADE, related_name="unipegaso_option_video_link")
    link =  models.CharField(max_length=100, blank=False, null=False)

    class Meta:
        verbose_name = '7_UnipegasoVideoOptionLink'
        verbose_name_plural = '7_UnipegasoVideoOptionLinks'

    def __str__(self):
        return f"{self.link}"
    
class UnipegasoActionItemsNextQuestionVideo(TimeStampModel):
    video_link = models.CharField(max_length=200, blank=False)
    unipegaso_next_question = models.ForeignKey(UnipegasoActionItemsNextQuestion, on_delete=models.CASCADE, related_name="unipegaso_next_videos")

    class Meta:
        verbose_name = '8_UnipegasoActionItemsNextQuestionVideo'
        verbose_name_plural = '8_UnipegasoActionItemsNextQuestionVideos'

    def __str__(self):
        return f"{self.video_link}"
    
class UnipagesoStudentPTMapper(TimeStampModel):
    unipegaso_test = models.ForeignKey(UnipegasoTest, on_delete=models.CASCADE, related_name="unipegaso_ptest_mapper")
    student_detail = models.ForeignKey(StudentDetail, on_delete=models.CASCADE, related_name="student_detail_ptest_mapper")
    rising_test_result = models.CharField(max_length=50, null=True, blank=True)
    is_completed = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        verbose_name = '9.1_UnipagesoStudentPTMapper'
        verbose_name_plural = '9.1_UnipagesoStudentPTMappers'

    @property
    def calculate_my_score(self):
        result = {}
        result[("R","Realistic")] = self.unipegaso_stu_mapper.filter(answer="Agree",unipegaso_question__question_category="Realistic").count()
        result[("I","Investigative")] = self.unipegaso_stu_mapper.filter(answer="Agree",unipegaso_question__question_category="Investigative").count()
        result[("A","Artistic")] = self.unipegaso_stu_mapper.filter(answer="Agree",unipegaso_question__question_category="Artistic").count()
        result[("S","Social")] = self.unipegaso_stu_mapper.filter(answer="Agree",unipegaso_question__question_category="Social").count()
        result[("E","Enterprising")] = self.unipegaso_stu_mapper.filter(answer="Agree",unipegaso_question__question_category="Enterprising").count()
        result[("C","Conventional")] = self.unipegaso_stu_mapper.filter(answer="Agree",unipegaso_question__question_category="Conventional").count()
        return result

    def link_to_unipegaso_student_pt_mapper(self):
        link=reverse("admin:unipegaso_unipagesostudentptmapper_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.student_detail.email}</a>') 

class UnipagesoStudentNextQuestionTracker(TimeStampModel):
    student_detail = models.ForeignKey(StudentDetail, on_delete=models.CASCADE, related_name="student_detail_nextquestion_mapper", blank=True, null=True)
    unipegaso_ai_next_question = models.ForeignKey(UnipegasoActionItemsNextQuestion, on_delete=models.CASCADE, related_name="unipegaso_next_question_tracker")
    answer = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = '9.3_UnipagesoStudentNextQuestionTracker'
        verbose_name_plural = '9.3_UnipagesoStudentNextQuestionTrackers'

    def link_to_tracker(self):
        link=reverse("admin:unipegaso_unipagesostudentnextquestiontracker_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.student_detail.email}</a>') 
    
class UnipegasoStudentPTAnswer(TimeStampModel):
    unipegaso_student_mapper = models.ForeignKey(UnipagesoStudentPTMapper, on_delete=models.CASCADE, related_name="unipegaso_stu_mapper")
    unipegaso_question = models.ForeignKey(UniPegasoActionItemsPTQuestion, on_delete=models.CASCADE, related_name="stu_unipegaso_question", blank=True, null=True)
    answer = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        verbose_name = '9.2_UnipegasoStudentPTAnswer'
        verbose_name_plural = '9.2_UnipegasoStudentPTAnswers'

    def __str__(self):
        return f"{self.unipegaso_question}"
    
    def link_to_link_to_answer(self):
        link = reverse("admin:unipegaso_unipegasostudentptanswer_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click</a>')