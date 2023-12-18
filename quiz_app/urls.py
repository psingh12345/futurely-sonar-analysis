from django.urls import path
from . import views

urlpatterns = [
    path('quiz/', views.QuizIndexView.as_view(), name='quiz_index'),
    path('quiz/start-quiz-test/<int:quiz_id>/', views.StartQuizView.as_view(), name='start_quiz'),
    path('quiz/time-out/', views.TimeOutView.as_view(), name='time_out'),
    path('quiz/final-result/', views.FinalResultView.as_view(), name='final_result'),
]