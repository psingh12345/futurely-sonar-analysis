from django.urls import path
from . import views

urlpatterns = [
    path('IFOA/orientamento/', views.IFOAIndexView.as_view(), name='ifoa_index'),
    path('IFOA/register/', views.IFOARegistrationView.as_view(), name='ifoa_register'),
    path('IFOA/pt-submit/', views.PTQuestionSubmitView.as_view(), name='pt_submit'),
    path('IFOA/final-slide/', views.IFOAFinalSlide.as_view(), name="ifoa_final_slide"),
    path('IFOA/Certificate/', views.IFOACertificateView.as_view(), name='ifoa_certificate'),
    path('IFOA/send-and-verify-otp', views.OTPSendAndVerificationView.as_view(), name='send_otp_and_verify'),
]