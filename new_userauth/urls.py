from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

# app_name = 'new_userauth'
urlpatterns = [
    path('register/', views.PersonRegisterView.as_view(), name="register"),
    path('login/', views.PersonloginView.as_view(), name="login"),
    path('password-reset/', views.RestPasswordEmailView.as_view(), name="landing_website_reset_password_email"),
    path('password_reset/done/', views.RestPasswordDoneView.as_view(), name="landing_website_done_reset_page"),
    path('reset/<uidb64>/<token>/', views.NewPasswordView.as_view(template_name="new_userauth/new_password.html"), name="landing_website_password_reset_confirm"),
    path('reset/done/', views.RestPasswordDoneView.as_view(), name="landing_website_password_reset_complete"),
    path('become-ambassdor/', views.BecomeAnAmbassador.as_view(), name="become_Ambassdor"),
]   
