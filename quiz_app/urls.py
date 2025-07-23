from django.urls import path
from . import views

app_name = 'quiz_app'

urlpatterns = [
    # Main quiz views
    path('', views.quiz_list, name='quiz_list'),
    path('categories/', views.categories, name='categories'),
    path('category/<int:category_id>/', views.category_quizzes, name='category_quizzes'),
    path('dashboard/', views.quiz_dashboard, name='dashboard'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),

    # Individual quiz views
    path('quiz/<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quiz/<uuid:quiz_id>/take/', views.take_quiz, name='take_quiz'),
    path('quiz/<uuid:quiz_id>/results/<uuid:attempt_id>/', views.quiz_results, name='quiz_results'),
    path('quiz/<uuid:quiz_id>/analytics/', views.quiz_analytics, name='quiz_analytics'),

    # AI Quiz generation (main feature)
    path('generate/', views.generate_ai_quiz, name='generate_ai_quiz'),

    # AJAX endpoints
    path('ajax/save-answer/', views.ajax_save_answer, name='ajax_save_answer'),
    path('ajax/submit-quiz/', views.ajax_submit_quiz, name='ajax_submit_quiz'),
]
