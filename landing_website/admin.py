from django.contrib import admin
from .models import LandingWebsiteFaqModel, LandingWebsitePrivacyPolicy, LandingWebsiteCookiesPolicy, LandingWebsiteTermsOfUse, Newsletter, ContactUs, NewsLetterPrivacyPolicy, RegisterPrivacyPolicy, WebsitePrivacyPolicy, TermsAndCondition, RegisterTermsAndCondition

# Register your models here.
@admin.register(LandingWebsiteFaqModel)
class LandingWebsiteFaqAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'locale']
    list_filter = ['locale',]


@admin.register(LandingWebsitePrivacyPolicy)
class LandingWebsitePrivacyPolicyAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content','download_pdf_file_link','locale']
    list_filter = ['locale',]


@admin.register(LandingWebsiteCookiesPolicy)
class LandingWebsiteCookiesPolicyAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content','download_pdf_file_link', 'locale']
    list_filter = ['locale',]


@admin.register(LandingWebsiteTermsOfUse)
class LandingWebsiteTermsOfUseAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'download_pdf_file_link','locale']
    list_filter = ['locale',]

@admin.register(TermsAndCondition)
class TermsAndConditionAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'download_pdf_file_link','locale']
    list_filter = ['locale',]

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['id', 'email', 'subscribe']
    list_filter = ['subscribe',]


@admin.register(ContactUs)
class ContactUsAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['first_name', 'last_name', 'email','organization','organization_name_other','role','concern','subscribe_newsletter', 'company_name', 'phone_number',]
    list_filter = ['organization',]



@admin.register(NewsLetterPrivacyPolicy)
class NewsLetterPrivacyPolicyAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'download_pdf_file_link','locale']
    list_filter = ['locale',]


@admin.register(RegisterPrivacyPolicy)
class RegisterPrivacyPolicyAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'download_pdf_file_link','locale']
    list_filter = ['locale',]


@admin.register(RegisterTermsAndCondition)
class RegisterTermsAndConditionAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'download_pdf_file_link','locale']
    list_filter = ['locale',]


@admin.register(WebsitePrivacyPolicy)
class WebsitePrivacyPolicyAdmin(admin.ModelAdmin):
    exclude = ['created_by', 'modified_by']
    list_display = ['sno', 'title', 'content', 'download_pdf_file_link','locale']
    list_filter = ['locale',]