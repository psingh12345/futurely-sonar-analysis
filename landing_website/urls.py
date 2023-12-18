from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path("", views.LandingWebsiteView.as_view(), name="index"), 
    path("about/", views.LandingWebsiteAboutView.as_view(), name="about"), 
    path("company/", views.LandingWebsiteCompanyView.as_view(), name="landing_website_company"), 
    path("mentor/", views.LandingWebsiteMentorView.as_view(), name="mentor"), 
    path("schools/", views.LandingWebsiteSchoolView.as_view(), name="school"), 
    path("university/", views.LandingWebsiteUniversityView.as_view(), name="landing_website_university"), 
    path("faq/", views.LandingWebsiteFaqView.as_view(), name="faq"),
    path("privacy-policy/", views.LandingWebsitePrivacyPolicyView.as_view(), name="privacy_policy"),
    path("terms-of-use/", views.LandingWebsiteTermsOfUseView.as_view(), name="terms_of_use"),
    path("cookies-policy/", views.LandingWebsiteCookiesPolicyView.as_view(), name="cookies_policy"),
    path("newsletter/", views.NewsletterFormView.as_view(), name="landing_website_newsletter"),
    path('download-pdf', views.DownloadPDFView.as_view(), name="download_pdf_cookies"),
    path("news-letter-policy/", views.NewsLetterPrivacyPolicyView.as_view(), name="news_letter_policy"),
    path("register-privacy-policy/", views.RegisterPrivacyPolicyView.as_view(), name="register_privacy_policy"),
    path("website-privacy-policy/", views.WebsitePolicyView.as_view(), name="website_privacy_policy"),
    path("terms-and-conditions/", views.TermsAndConditionsView.as_view(), name="terms_and_conditions"),
    path("register-terms-and-conditions/", views.RegisterTermsAndConditionView.as_view(), name="register_terms_and_conditions"),

]