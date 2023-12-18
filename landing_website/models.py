from django.db import models
from courses.models import LogBaseModel
from ckeditor.fields import RichTextField




CHOICE_LANG = [
    ("en-us", "English"),
    ("it", "Italiano")
]

class LandingWebsiteFaqModel(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
        
    class Meta:
        verbose_name = 'LandingWebsiteFaq'
        verbose_name_plural = 'LandingWebsitesFaq'


class LandingWebsitePrivacyPolicy(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
        
    class Meta:
        verbose_name = 'LandingWebsitePrivacyPolicy'
        verbose_name_plural = 'LandingWebsitesPrivacyPolicy'

    

class LandingWebsiteCookiesPolicy(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
    
        
    class Meta:
        verbose_name = 'LandingWebsiteCookiesPolicy'
        verbose_name_plural = 'LandingWebsitesCookiesPolicy'


class LandingWebsiteTermsOfUse(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)

        
    class Meta:
        verbose_name = 'LandingWebsiteTermsOfUse'
        verbose_name_plural = 'LandingWebsitesTermsOfUse'

class TermsAndCondition(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
        
    class Meta:
        verbose_name = 'TermsAndCondition'
        verbose_name_plural = 'TermsAndConditions'


class Newsletter(LogBaseModel):
    email = models.EmailField(max_length=254,null=False,blank=False)
    subscribe = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Newsletter'
        verbose_name_plural = 'Newsletters'



class ContactUs(LogBaseModel):

    ORGANIZATION_CHOICES = [
        ('Scuola', 'Scuola'),
        ('Università', 'Università'),
        ('Azienda', 'Azienda'),
        ('Altro', 'Altro'),
        
    ]

    first_name = models.CharField(max_length=100,null=False,blank=False)
    last_name = models.CharField(max_length=100, name=False, blank=False)
    email = models.EmailField(max_length=50,null=False, blank=False)
    organization = models.CharField(max_length=100, choices=ORGANIZATION_CHOICES, null=False, blank=False)
    organization_name_other = models.CharField(max_length=100, null=True, blank=True)
    role = models.CharField(max_length=50,null=False, blank=False)
    concern = models.TextField(null=False, blank=False)
    subscribe_newsletter = models.BooleanField(default=False)
    company_name = models.CharField(max_length=50, null=True, blank=True)
    phone_number = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = 'ContactUs'
        verbose_name_plural = 'ContactUs'

    def __str__(self):
         return f"{self.email} -> {self.role}"
    


class NewsLetterPrivacyPolicy(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
    
        
    class Meta:
        verbose_name = 'NewsLetterPrivacyPolicy'
        verbose_name_plural = 'NewsLetterPrivacyPolicies'


class RegisterPrivacyPolicy(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
    
        
    class Meta:
        verbose_name = 'RegisterPrivacyPolicy'
        verbose_name_plural = 'RegisterPrivacyPolicies'

class RegisterTermsAndCondition(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'RegisterTermsAndCondition'
        verbose_name_plural = 'RegisterTermsAndConditions'


class WebsitePrivacyPolicy(LogBaseModel):
    sno = models.IntegerField(blank=True, null=True, default=1)
    title = models.TextField()
    content = RichTextField(blank=True, null = True)
    locale = models.CharField(
        max_length=20, default="it", blank=True, choices=CHOICE_LANG)
    download_pdf_file_link = models.URLField(null=True, blank=True)
    
        
    class Meta:
        verbose_name = 'WebsitePrivacyPolicy'
        verbose_name_plural = 'WebsitePrivacyPolies'
