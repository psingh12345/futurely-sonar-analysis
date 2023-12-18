from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.urls import reverse
from django.utils.html import format_html
# import courses.models as courses_models

# ARE_YOU_STUDENT = [
#     ("Yes", _("Yes")),
#     ("No", _("No")),
# ]

# ARE_YOU_14_PLUS = [
#     ("Yes", _("Yes")),
#     ("No", _("No")),
# ]

# ARE_YOU_FROM_FUTURELABS = [
#     ("Yes", _("Yes")),
#     ("No", _("No")),
# ]

# ARE_YOU_COMPANY_WELFARE_PROGRAM = [
#     ("Yes", _("Yes")),
#     ("No", _("No")),
# ]


# CLASS_YEAR_USA = [
#     ('Select Class Year', 'Select Class Year'),
#     ("1st Year", "1st Year"),
#     ("2nd Year", "2nd Year"),
#     ("3rd Year", "3rd Year"),
#     ("4th Year", "4th Year"),
#     ("5th Year", "5th Year"),
# ]

# CLASS_YEAR_ITALY = [
#     (_('Select Class Year'), _('Select Class Year')),
#     ("1st Year", "1st Year"),
#     ("2nd Year", "2nd Year"),
#     ("3rd Year", "3rd Year"),
#     ("4th Year", "4th Year"),
#     ("5th Year", "5th Year"),
# ]

# CLASS_NAME_USA = [
#     ('Select Class Name', 'Select Class Name'),
#     ("A Class", "A Class"),
#     ("B Class", "B Class"),
#     ("D Class", "D Class"),
# ]

# CLASS_NAME_ITALY = [
#     (_('Select Class Name'), _('Select Class Name')),
#     ("A Class", "A Class"),
#     ("B Class", "B Class"),
#     ("C Class", "C Class"),
# ]

# SPECIALIZATION_USA = [
#     ('Class Specialization', 'Class Specialization'),
#     ("X", "X"),
#     ("Y", "Y"),
# ]

# SPECIALIZATION_ITALY = [
#     (_('Class Specialization'), _('Class Specialization')),
#     ("Liceo - artistico", "Liceo - artistico"),
#     ("Liceo - classico", "Liceo - classico"),
#     ("Liceo - linguistico", "Liceo - linguistico"),
#     ("Liceo - musicale", "Liceo - musicale"),
#     ("Liceo - scientifico", "Liceo - scientifico"),
#     ("Liceo - scientifico scienze applicate", "Liceo - scientifico scienze applicate"),
#     ("Liceo - scientifico sportivo", "Liceo - scientifico sportivo"),
#     ("Liceo - scientifico tecnologico", "Liceo - scientifico tecnologico"),
#     ("Liceo - economico sociale", "Liceo - economico sociale"),
#     ("Liceo - scienze umane", "Liceo - scienze umane"),
#     ("Istituto tecnico", "Istituto professionale"),
#     ("Altro", "Altro"),
# ]

CHOICES_YES_NO = [
    ("Yes", _("Yes")),
    ("No", _("No")),
]

COUNTRIES = [
    ("USA", ("USA")),
    ("Italy", ("Italy")),
]

SRC_CHOICES = [
    ("future_lab", ("future_lab")),
    ("company", ("company")),
    ("general", ("general")),
]


class TimeStampModel(models.Model):
    """TimeStamp Model"""
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    modified_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        abstract = True


class School(TimeStampModel):
    name = models.CharField(max_length=200, blank=False, null=False)
    region = models.CharField(max_length=200, blank=False, null=False)
    city = models.CharField(max_length=200, blank=False, null=False)
    type = models.CharField(max_length=200, blank=False, null=False)
    country = models.CharField(
        max_length=70, default='Italy', choices=COUNTRIES)
    is_verified = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'School'
        verbose_name_plural = 'Schools'

    def __str__(self):
        return "{}".format(self.name)


class CountryDetails(TimeStampModel):
    region = models.CharField(max_length=200, blank=False, null=False)
    city = models.CharField(max_length=200, blank=False, null=False)
    country = models.CharField(
        max_length=70, default='Italy', choices=COUNTRIES)

    class Meta:
        verbose_name = 'CountryDetail'
        verbose_name_plural = 'CountryDetails'

    def __str__(self):
        return f"{self.region}:{self.city}"


class Company(TimeStampModel):
    name = models.CharField(max_length=200, blank=False, null=False)
    country = models.CharField(
        max_length=70, default='Italy', choices=COUNTRIES)

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'

    def __str__(self):
        return "{}".format(self.name)

class CompanyDetail(TimeStampModel):
    company = models.OneToOneField(Company, on_delete=models.CASCADE, related_name="company_detail")
    is_display_specific_job_posts = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Company Detail'
        verbose_name_plural = 'Company Details'

    def __str__(self):
        return "{}".format(self.company)

class ClassYear(TimeStampModel):
    name = models.CharField(max_length=200, blank=False, null=False)
    year_sno = models.IntegerField(default=0, blank=False, null=False)
    country = models.CharField(
        max_length=70, default='Italy', choices=COUNTRIES)

    class Meta:
        ordering = ['year_sno',]
        verbose_name = 'ClassYear'
        verbose_name_plural = 'ClassYears'

    def __str__(self):
        return "{}".format(self.name)


class ClassName(TimeStampModel):
    name = models.CharField(max_length=200, blank=False, null=False)
    name_sno = models.IntegerField(default=0, blank=False, null=False)
    country = models.CharField(
        max_length=70, default='Italy', choices=COUNTRIES)

    class Meta:
        ordering = ['name',]
        verbose_name = 'ClassName'
        verbose_name_plural = 'ClassNames'

    def __str__(self):
        return "{}".format(self.name)


class Specialization(TimeStampModel):
    name = models.CharField(max_length=200, blank=False, null=False)
    country = models.CharField(
        max_length=70, default='Italy', choices=COUNTRIES)

    class Meta:
        verbose_name = 'Specialization'
        verbose_name_plural = 'Specializations'

    def __str__(self):
        return "{}".format(self.name)


CHOICES_HOW_KNOW_US = [
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
    ("Other", _("Other")),
]

CHOICES_GENDER = [
    ("Male", _("Male")),
    ("Female", _("Female")),
    ("Other", _("Other"))
]

CHOICE_Lang = [
    ("en-us", "English"),
    ("it", "Italiano")
]


class Person(AbstractUser, TimeStampModel):
    """User Model"""
    first_name = models.CharField(max_length=100, blank=False)
    last_name = models.CharField(max_length=100, blank=False)
    email_verified = models.BooleanField(default=False)
    contact_number = models.CharField(max_length=20, blank=True, null=True)
    how_know_us = models.CharField(
        max_length=20, blank=True, null=True, choices=CHOICES_HOW_KNOW_US)
    how_know_us_other = models.CharField(max_length=100, blank=True, null=True)
    last_visit = models.DateTimeField(default=timezone.now)
    gender = models.CharField(
        max_length=20, blank=True, null=True, choices=CHOICES_GENDER)
    gender_other = models.CharField(
        max_length=100, blank=True, null=True, default='')
    country_name = models.CharField(
        max_length=30, blank=True, null=True, default='')
    lang_code = models.CharField(
        max_length=20, blank=True, null=True, choices=CHOICE_Lang)
    clarity_token = models.CharField(max_length=100, blank=True, null=True)

    def link_to_person(self):
        link = reverse("admin:userauth_person_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')

    @property
    def person_role(self):
        if hasattr(self, 'student'):
            return 'Student'
        elif hasattr(self, 'counselor'):
            return 'Counselor'
        else:
            return 'Futurely_admin'

    @property
    def is_linked_to_counselor_special_dashboard(self):
        try:
            self.counselor.counselorwithspecialdashboard
            return True
        except Exception as e:
            return False

    class Meta:
        verbose_name = 'Person'
        verbose_name_plural = 'Persons'

    def __str__(self):
        return "{} {}".format(self.first_name, self.last_name)


class Student(TimeStampModel):
    person = models.OneToOneField(
        Person, related_name="student", on_delete=models.CASCADE)
    are_you_a_student = models.CharField(
        max_length=30, default='Yes', null=True, blank=True, choices=CHOICES_YES_NO)
    are_you_fourteen_plus = models.CharField(
        max_length=30, default='No', null=False, blank=True, choices=CHOICES_YES_NO)
    # are_you_from_futurelabs = models.CharField(max_length=70, default='No', null=False, blank=True, choices=CHOICES_YES_NO)
    # are_you_part_of_company_welfare_program = models.CharField(max_length=70, default='No', null=False, blank=True, choices=CHOICES_YES_NO)
    company = models.ForeignKey(
        Company, on_delete=models.DO_NOTHING, related_name="students", blank=True, null=True)
    discount_coupon_code = models.CharField(
        max_length=50, default='', null=True, blank=True)
    future_lab_form_status = models.BooleanField(default=False)
    src = models.CharField(max_length=50, default='general',
                           null=True, blank=True, choices=SRC_CHOICES, verbose_name='Source')
    number_of_offered_plans = models.CharField(
        max_length=10, default='3', blank=True, null=True)
    skip_course_dependency = models.BooleanField(
        default=False, blank=True, null=True)
    is_course1_locked = models.BooleanField(
        default=False, blank=True, null=True)
    display_discounted_price_only = models.BooleanField(
        default=False, blank=True, null=True)
    total_pcto_hours = models.IntegerField(default=0, blank=True, null=True)
    is_welcome_video_played = models.BooleanField(default=False)
    is_step1_pdf_downloaded = models.BooleanField(default=False)
    is_from_middle_school = models.BooleanField(
        default=False, blank=True, null=True)
    is_from_fast_track_program = models.BooleanField(
        default=False, blank=True, null=True)
    student_channel = models.CharField(
        max_length=50, default='free_channel', null=True, blank=True)
    privacy_policy_mandatory = models.BooleanField(default=False)
    accept_tracking = models.BooleanField(default=False)
    accept_data_third_party = models.BooleanField(default=False)
    accept_marketing = models.BooleanField(default=False)
    age = models.CharField(max_length=20, blank=True, null=True)
    sponsor_compnay = models.ForeignKey(Company,on_delete=models.DO_NOTHING , related_name ="stu_sponsor_company",blank=True , null= True)


    def update_total_pcto_hour(self):
        total_hours = 0
        my_webinars_pcto = self.student_pcto_record.all()
        if my_webinars_pcto.count() > 0:
            for webinar_pcto in my_webinars_pcto:
                total_hours = total_hours + webinar_pcto.pcto_hours
            self.total_pcto_hours = total_hours
            self.save()

    def is_webinar_joined(self, webinar):
        my_webinar = self.student_webinar_record.all().filter(webinar=webinar)
        if my_webinar.count() == 0:
            return False
        else:
            return True

    def link_student(self):
        link = reverse("admin:userauth_student_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">Click here</a>')
    
    def is_any_pending_comment_to_read(self):
        result = False
        try:
            student_cohorts = self.person.stuMapID.all()
            for student_cohort in student_cohorts:
                cohort_result = student_cohort.is_any_pending_diary_comment_to_read()
                if cohort_result:
                    result = True
                    break
        except:
            result = False
        return result

    class Meta:
        verbose_name = 'Student'
        verbose_name_plural = 'Students'

    def __str__(self):
        return "{}".format(self.person)


class Counselor(TimeStampModel):
    person = models.OneToOneField(
        Person, related_name="counselor", on_delete=models.CASCADE)
    school_region = models.CharField(max_length=50, blank=True, default='')
    school_city = models.CharField(max_length=50, blank=True, default='')
    school_name = models.CharField(max_length=100, blank=True, default='')
    is_verified_by_futurely = models.BooleanField(default=False)
    company = models.ForeignKey(
        Company, on_delete=models.DO_NOTHING, related_name="counselors", blank=True, null=True)
    academic_session_start_date = models.DateField(
        default="2022-08-01", editable=True)
    plans = models.ManyToManyField("courses.OurPlans", blank=True, null=True)
    coupon_code = models.CharField(
        max_length=50, default='', null=True, blank=True)
    is_for_fast_track_program_only = models.BooleanField(
        default=False, blank=True, null=True)
    is_for_middle_school_only = models.BooleanField(
        default=False, blank=True, null=True)
    is_trial_account = models.BooleanField(
        default=False, blank=True, null=True)
    course_module = models.ForeignKey(
        'courses.Modules', on_delete=models.DO_NOTHING, related_name="counselors", blank=True, null=True)

    class Meta:
        verbose_name = 'Counselor'
        verbose_name_plural = 'Counselors'

    def __str__(self):
        return "{}".format(self.person)


class CounselorWithSpecialDashboard(TimeStampModel):
    counselor = models.OneToOneField(Counselor, on_delete=models.CASCADE)


class FuturelyAdmin(TimeStampModel):
    person = models.OneToOneField(
        Person, related_name="futurely_admins", on_delete=models.CASCADE)

    def link_to_futurelyadmin(self):
        link = reverse("admin:userauth_futurelyadmin_change", args=[self.id])
        print(link)
        return format_html(f"<a href='{link}' target='_blank'>Click here</a>")

    class Meta:
        verbose_name = 'FuturelyAdmin'
        verbose_name_plural = 'FuturelyAdmins'

    def __str__(self):
        return "{}".format(self.person)


class StudentSchoolDetail(TimeStampModel):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="student_school_detail")
    class_year = models.ForeignKey(
        ClassYear, on_delete=models.DO_NOTHING, null=True, related_name="student_school_details")
    class_name = models.ForeignKey(
        ClassName, on_delete=models.DO_NOTHING, null=True, related_name="student_school_details")
    specialization = models.ForeignKey(
        Specialization, on_delete=models.DO_NOTHING, null=True, blank=True, related_name="student_school_details")
    school_region = models.CharField(max_length=50, blank=True, default='')
    school_city = models.CharField(max_length=50, blank=True, default='')
    school_name = models.CharField(max_length=100, blank=True, default='')
    school_type = models.CharField(max_length=150, blank=True, default='')
    graduation_year = models.CharField(max_length=30, blank=True, default='')

    def link_to_studentschooldetail(self):
        link = reverse(
            "admin:userauth_studentschooldetail_change", args=[self.id])
        return format_html(f'<a href="{link}" target="_blank">{self.student.person.username}</a>')

    class Meta:
        verbose_name = 'StudentSchoolDetail'
        verbose_name_plural = 'StudentSchoolDetails'

    def __str__(self):
        return "{}".format(self.student)


class StudentParentsDetail(TimeStampModel):
    student = models.OneToOneField(
        Student, on_delete=models.CASCADE, related_name="student_parent_detail")
    parent_name = models.CharField(max_length=20, blank=True, null=True)
    parent_contact_number = models.CharField(
        max_length=20, blank=True, null=True)
    parent_email = models.CharField(max_length=100, default='', blank=False)
    parent_email_from_reg = models.CharField(
        max_length=100, default='', blank=True)

    class Meta:
        verbose_name = 'StudentParentsDetail'
        verbose_name_plural = 'StudentParentsDetails'


class Payment(TimeStampModel):
    payment_intent_id = models.CharField(max_length=200, blank=False)
    name = models.CharField(max_length=200, default='', blank=False)
    email = models.CharField(max_length=100, default='', blank=False)
    amount = models.CharField(max_length=10, blank=False)
    status = models.CharField(max_length=30, default='', blank=False)

    class Meta:
        verbose_name = 'Payment'
        verbose_name_plural = 'Payments'

    def __str__(self):
        return "{}".format(self.payment_intent_id)


# requested, proceeded
STUDENT_DELETE_STATUS = [
    ('Requested', 'Requested'),
    ('Processed', 'Processed'),
]


class StudentDeleteRequest(TimeStampModel):
    student = models.ForeignKey(
        Person, related_name="delete_students", on_delete=models.DO_NOTHING)
    subject = models.CharField(max_length=100, null=True, blank=True)
    reason_message = models.TextField(max_length=500, null=True, blank=True)
    lang_code = models.CharField(
        max_length=20, blank=True, null=True, choices=CHOICE_Lang)
    is_status = models.CharField(
        max_length=20, default="Requested", choices=STUDENT_DELETE_STATUS)

    class Meta:
        verbose_name = 'StudentDeleteRequest'
        verbose_name_plural = 'StudentsDeleteRequest'


COMPANY_PATH_CHOICE = [
    ('BOTH', 'BOTH'),
    ('Middle School', 'Middle School'),
    ('High School', 'High School'),
]


class CompanyWithSchoolDetail(TimeStampModel):
    company = models.OneToOneField(Company, on_delete=models.CASCADE)
    company_path_type = models.CharField(
        default="", choices=COMPANY_PATH_CHOICE, max_length=50, null=True, blank=True)

    def __str__(self) -> str:
        return f"{self.company.name} - {self.company_path_type}"

    class Meta:
        verbose_name = 'CompanyWithSchoolDetail'
        verbose_name_plural = 'CompanyWithSchoolDetails'


class MasterOTP(TimeStampModel):
    otp = models.CharField(max_length=30)

    class Meta:
        verbose_name = 'MasterOTP'
        verbose_name_plural = 'MasterOTPS'

    def __str__(self):
        return "{}".format(self.otp)


class HubspotCredential(models.Model):
    """
    HubspotCredential Model
    This model is used to store the credentials for Hubspot.
    """

    title = models.CharField(max_length=120)
    value = models.CharField(max_length=120)

    class Meta:
        """Meta Class"""

        verbose_name = 'HubspotCredential'
        verbose_name_plural = 'HubspotCredentials'
