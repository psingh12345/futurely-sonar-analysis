from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    # ###########################################################################################################
    # ###########################################################################################################
    path("unipegaso/assessment/", views.UniPegasoIndexView.as_view(), name="unipegaso_index"), 
    path("unipegaso/register/", views.RegisterPageView.as_view(), name="unipegaso_register"), 
    path("unipegaso/finish-slide/", views.FinishSlideView.as_view(), name="finish_slide"),
    path('unipegaso/pt-submit-answer/', views.pt_test_submit, name="pt_test_submit"),
    path('unipegaso/certificate/', views.CertificateView.as_view(), name="certificate"),
    
    # ###########################################################################################################
    # ###########################################################################################################
    path("unimercatorum/assessment/", views.UniMercatorumView.as_view(), name="unimercatorum_index"),
    path("unimercatorum/register/", views.UniMercatorumRegisterPageView.as_view(), name="unimercatorum_register"), 
    path("unimercatorum/finish-slide/", views.UniMercatorumFinishSlideView.as_view(), name="unimercatorum_finish_slide"),
    path('unimercatorum/certificate/', views.UniMercatorumCertificateView.as_view(), name="unimercatorum_certificate"),
    # ###########################################################################################################
    # ###########################################################################################################
    # ###########################################################################################################
    # ###########################################################################################################
    path("utsanraffaele/assessment/", views.UTSanRaffaeleView.as_view(), name="utsanraffaele_index"),
    path("utsanraffaele/register/", views.UTSanRaffaeleRegisterPageView.as_view(), name="utsanraffaele_register"),
    path("utsanraffaele/finish-slide/", views.UTSanRaffaeleFinishSlideView.as_view(), name="utsanraffaele_finish_slide"),
    path('utsanraffaele/certificate/', views.UTSanRaffaeleCertificateView.as_view(), name="utsanraffaele_certificate"),
    # ###########################################################################################################
    # ###########################################################################################################
]
