from django.contrib import admin
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    #path('courses-overview/',views.course_overview,name='courses-overview'),
    # path('counselor-dashboard/',views.counselor_dashboard_view,name='counselor-dashboard'),
    # path('student-performance/', views.counselor_stu_performance, name = "student-performance"),
    # path("bulk_email_panel/", views.bulk_email_panel_view, name="bulk_email_panel_view"),
    # path("save_excel_file/", views.save_excel_file, name="save_excel_file"),
    # path("email_tracking_dashboard/", views.get_dynamodb, name="email_tracking_dashboard"),
    # path("excelfiledownload/", views.excelfiledownload, name="excelfiledownload"),
    # path("students-kpis/", views.student_performace_for_counselor_view, name="students_kpis"),
    # path("scholarship-students-information/", views.scholarship_information_view, name="scholarship_students_information"),
    # path("student-scholarship-details/", views.student_scholarship_detail, name="student_scholarship_details"),
    # path("scholarship-approved/", views.scholarship_approved_view, name="scholarship_approved"),
    # path("scholarship-declied/", views.declied_scholarship_view, name="scholarship_declied"),
    # path("send-push-notification/", views.send_push_notification_view, name='send_push_notification'),
    # path("send-push-notification-by-cohort/", views.PushNotificationByCohort.as_view(), name='send_push_notification_by_cohort'),
    # path("submit-comment/", views.submit_comment_view, name="submit_comment"),
    # path("getcohort/", views.cohortfilter, name="cohortfilter"),
    # path("cohort-details/", views.cohort_details, name="cohort_details"),
    # path("students-step-detail/<cohort_id>/<step_status_id>/", views.students_step_detail, name="students_step_detail"),
    # path("student-course-report/", views.StudentCourseReport.as_view(), name="student_course_report"),
    # path("download-csv/", views.CSVDownloadForCousnelorView.as_view(), name="create_csv"),
]