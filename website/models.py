from email.policy import default
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from userauth.models import Person
import datetime
from django.db.models.base import Model
from courses.models import LogBaseModel
from django.utils.html import format_html
from ckeditor.fields import RichTextField

CHOICE_LANG = [
    ("en-us", "English"),
    ("it", "Italiano")
]


class ModuleManager(models.Manager):
    def get_queryset(self):
        return super(ModuleManager, self).get_queryset()

    def lang_code(self, lang):
        return super(ModuleManager, self).get_queryset().filter(module_lang=lang)


class FaqModel(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
        
    class Meta:
        managed = True

# Create your models here.
class Webinars(LogBaseModel):
    title = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    publish_date = models.DateTimeField(default=timezone.now)
    icon = models.FileField(upload_to='images', blank=True)
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    objects = models.Manager()  # The default manager.
    published = ModuleManager()  # Our custom manager.
    
    class Meta:
        ordering = ('publish_date',)
        verbose_name = 'Webinars'
        verbose_name_plural = 'Webinars'
    def __str__(self):
        return self.title

class MentorsInfo(LogBaseModel):
    m_name = models.CharField(max_length=250)
    title = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    icon = models.FileField(upload_to='images', blank=True)
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    objects = models.Manager()  # The default manager.
    published = ModuleManager()  # Our custom manager.
    
    class Meta:
        verbose_name = 'MentorInfo'
        verbose_name_plural = 'MentorsInfo'
    def __str__(self):
        return self.m_name
        

STATUS_CHOICES = [
    ("Open", ("Open")),
    ("Closed", ("Closed")),
]

class Query(LogBaseModel):
    person = models.ForeignKey(Person, related_name="person", on_delete=models.CASCADE, null=True)
    name = models.CharField(max_length=100, default='', blank=True)
    email = models.EmailField(max_length=100, default='', blank=True)
    message = models.TextField(default='', blank=True)
    status = models.CharField(max_length=50, default='Open', blank=True, choices=STATUS_CHOICES)
    class Meta:
        verbose_name = 'Query'
        verbose_name_plural = 'Queries'

    def __str__(self):
        if self.person:
            return "{}".format(self.person)
        return "{} | {}".format(self.name, self.email)

CHOICE_TESTIMONIAL = [
    ("Student", "Student"),
    ("School", "School")
]

class DiamnodQuery(LogBaseModel):
    person = models.ForeignKey(Person, related_name="diamond_queries", on_delete=models.CASCADE, null=True)
    email = models.EmailField(max_length=100, default='', blank=True)
    phone_num = models.CharField(max_length = 20, default = '', blank=True)
    status = models.CharField(max_length=50, default='Open', blank=True, choices=STATUS_CHOICES)
    class Meta:
        verbose_name = 'DiamnodQuery'
        verbose_name_plural = 'DiamnodQueries'

    def __str__(self):
        if self.person:
            return "{}".format(self.person)
        return "{} | {}".format(self.email, self.phone_num)

class Testimonials(LogBaseModel):
    name = models.CharField(max_length=250)
    designation = models.CharField(max_length=250)
    category = models.CharField(max_length=250,default='',blank=True, choices=CHOICE_TESTIMONIAL)
    feedback = models.TextField(null=True, blank=True)
    icon = models.FileField(upload_to='images', blank=True)
    module_lang = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    objects = models.Manager()  # The default manager.
    published = ModuleManager()  # Our custom manager.
    
    class Meta:
        verbose_name = 'Testimonial'
        verbose_name_plural = 'Testimonials'
    def __str__(self):
        return self.name

class Files(LogBaseModel):
    file = models.FileField(upload_to="downloadable_files",blank=True,null=True)
    title = models.CharField(max_length=50,blank=True, default='', null=True)
    
    def fileLink(self):
        if self.file:
            return format_html(f"<a href='{self.file.url}' download='{self.file.url}'>{self.title}</a>")
        else:
            return format_html('<a href="''"></a>')

    class Meta:
        verbose_name = 'file'
        verbose_name_plural = 'files'
    def __str__(self):
        return self.title

class ParentInfo(LogBaseModel):
    parent_name = models.CharField(max_length=250,blank=True)
    parent_email = models.EmailField(max_length=250)
    child_name = models.CharField(max_length=250,blank=True)
    child_email = models.EmailField(max_length=250,blank=True)
    child_number = models.CharField(max_length=20,blank=True,default='')
    company_name = models.CharField(max_length=250, blank=True)
    school_path = models.CharField(max_length=50, blank=True)
    
    class Meta:
        verbose_name = 'ParentInfo'
        verbose_name_plural = 'ParentInfos'
    def __str__(self):
        return self.parent_name

COOKIES_SELECTED_SECTION_CHOICES = [
    ("Banner", "Banner"),
    ("Popup", "Popup"),
]

class CookiesSelectedData(LogBaseModel):
    clarity_id = models.CharField(max_length=250, blank=True)
    custom_session_id = models.CharField(max_length=250, blank=True)
    cookies_necessari = models.BooleanField(default=False)
    cookies_esperienza = models.BooleanField(default=False)
    cookies_misurazione = models.BooleanField(default=False)
    cookies_selected_section = models.CharField(max_length=50, blank=True, choices=COOKIES_SELECTED_SECTION_CHOICES)

    class Meta:
        verbose_name = 'CookiesSelectedData'
        verbose_name_plural = 'CookiesSelectedData'
    def __str__(self):
        return self.clarity_id