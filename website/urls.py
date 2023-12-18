from os import name
from django.contrib import admin
from django.urls import path
from . import views


urlpatterns = [
    # path('', views.LandingPageView.as_view(), name="index"),
    path('ios/',views.LandingPageIOSView.as_view(), name="IOSindex"),
    # path('index-light/', views.LandingPageView_light.as_view(), name="index_light"),
    # path('about/', views.AboutView.as_view(), name="about"),
    # path('schools/', views.SchoolView.as_view(), name="school"),
    # path('students/', views.StudentView.as_view(), name="student"),
    # path('lets-talk-send-message/', views.lets_talk_send_message, name="lets-talk-send-message"),
    # path('contact-for-diamond-plan/', views.contact_dimond_queries, name="contact-for-diamond-plan"),
    # path('mentor/', views.MentorView.as_view(), name="mentor"),
    # path('plans/', views.PriceView.as_view(), name="plans"),
    path("download_file/<int:file_id>/",views.file_download_view,name="download_file"),
    path("health/", views.health_check_view, name = "health"),
    path("set-lang/", views.set_lang_view, name="set_lang"),
    path("select-lang/", views.select_lang_at_initial_view, name="select_lang"),
    path("robots.txt", views.robots_txt),
    path("cookie-accept/", views.cookie_accept_view, name="cookie_accept"),
    path("cookie-data-save/", views.cookies_data_save_view, name="cookie_data_save"),
    # path("terms-of-use/", views.terms_of_use, name="terms_of_use"),
    # path("cookies-policy/", views.cookies_policy, name="cookies_policy"),
    # path("privacy-policy/", views.privacy_policy, name="privacy_policy"),
    # path("faq/", views.FaqRecord.faq, name="faq"),
    path("parents-info/",views.collect_student_parents_info, name="parents_info"),
]
