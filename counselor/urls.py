from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('programs/', views.counselor_select_program_view, name="counselor_program"),
    path('counselor-search/', views.counselor_search_view, name="counselor_search"),
    path('dashboard/', views.counselor_dashboard_view, name="counselor-dashboard"),
    path("students-kpis/", views.student_performace_for_counselor_view, name="students_kpis"),
    path("student-course-report/", views.StudentCourseReport.as_view(), name="student_course_report"),
    path('account-settings-counselor/', views.account_settings_view_counselor, name="account-settings-counselor"),
    # path('cohort-filter/', views.cohort_filter_view, name="cohort_filter"),
    path('select-program/', views.select_program_view, name="select_program"),
    path('class-section-students/', views.ClassSectionListView.as_view(), name="class_section_students"),
    path('student-details/', views.SingleStudentDetailView.as_view(), name="student_details"),
    path('middle-school-dashboard/', views.MiddleSchoolDashBoardView.as_view(), name="middle_school_dashboard"),
    path('get-diary-ques-answer/', views.get_diary_ques_answer, name="get_diary_ques_answer"),
    ]