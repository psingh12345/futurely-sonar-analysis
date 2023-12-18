from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# app_name = 'userauth'
urlpatterns = [
    # path('register/', views.PersonRegistrationView.as_view(), name="register"),
#     path('futurelab-register/', views.PersonFutureLabRegistrationView.as_view(), 
#           name="futurelab_register"),
    path("futurelab-register/", views.NewSingupView.as_view(), name="futurelab_signup_new"),
    path("user-from-ios/<str:plan_name>/", views.user_from_ios_view, name ="user_from_ios_view"),
    path("otp_verification", views.otp_verification, name="otp_verification"),
    path('email-sent/', views.email_sent_view, name="email-sent"),
    path('email-not-verified/', views.email_not_verified_view,
         name="email-not-verified"),
    path('verify_email/', views.email_verify_view, name="verify_email"),
    path('email_activate/<uidb64>/<token>/',
         views.EmailActivateView.as_view(), name="email_activate"),
    # path('login/', views.LoginView.as_view(), name="login"),
    path('logout/', views.LogoutView.as_view(), name="logout"),
    path('password_reset/',views.password_reset,name='password_reset'),
    # path('password_reset/done/',auth_views.PasswordResetDoneView.as_view(template_name="userauth/pass_reset/password_reset_done.html"),name='password_reset_done'),
    #path('reset/<uidb64>/<token>/',auth_views.PasswordResetConfirmView.as_view(template_name="userauth/password_reset_confirm.html"),name='password_reset_confirm'),
    # path('reset/<uidb64>/<token>/',views.SetPasswordView.as_view(template_name="userauth/pass_reset/password_reset_confirm.html"),name='password_reset_confirm'),
    # path('reset/done/',auth_views.PasswordResetCompleteView.as_view(template_name="userauth/pass_reset/password_reset_complete.html"),name='password_reset_complete'),
    path('coupon-code-exists/', views.coupon_code_exists, name="coupon-code-exists"),
    path('get-school-by-name/', views.get_school_details_by_name, name="get-school-by-name"),
    path('get-school-cities-name/', views.get_school_cities_by_region, name="get-school-cities-name"),
    path('get-school-name-by-city/', views.get_school_names_by_city_and_region, name="get-school-name-by-city"),
    path('counselor-login/', views.CounselorLoginView.as_view(), name="counselor_login"),
    path('admin-login/', views.AdminLoginView.as_view(), name="admin_login"),
    path('counselor-registration/', views.CounselorRegistrationView.as_view(), name="counselor_registration"),
    path('check-email/', views.check_email_view, name="check_email"),
    path('student-acccount-delete-request/', views.delete_student_account_view, name="stu_acccount_delete_request"),
    path('check-master-code/', views.check_master_code, name="check_master_code"),
    path("generate-otp/", views.generate_otp, name="generate_otp"),
    path("futurelab-register-create-custom-event", views.futurelab_register_create_custom_event, name="create_custom_event"),
    path("middle-school-registration/", views.MiddleSchoolRegistration.as_view(), name="middle_school_registration"),
    path("check-coupon/",views.check_coupon_view , name = "check-coupon"),
]
