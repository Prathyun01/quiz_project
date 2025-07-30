from django.urls import path
from . import views

app_name = 'admin_quiz'

urlpatterns = [
    # Dashboard
    path('', views.admin_dashboard, name='dashboard'),
    
    # Quiz management
    path('quizzes/', views.quiz_list, name='quiz_list'),
    path('quizzes/create/', views.create_quiz, name='create_quiz'),
    path('quizzes/<uuid:quiz_id>/', views.quiz_detail, name='quiz_detail'),
    path('quizzes/<uuid:quiz_id>/edit/', views.edit_quiz, name='edit_quiz'),
    path('quizzes/<uuid:quiz_id>/delete/', views.delete_quiz, name='delete_quiz'),
    path('quizzes/<uuid:quiz_id>/duplicate/', views.duplicate_quiz, name='duplicate_quiz'),
    path('quizzes/<uuid:quiz_id>/preview/', views.preview_quiz, name='preview_quiz'),
    path('quizzes/<uuid:quiz_id>/publish/', views.publish_quiz, name='publish_quiz'),
    path('quizzes/<uuid:quiz_id>/analytics/', views.quiz_analytics, name='quiz_analytics'),
    
    # Question management
    path('quizzes/<uuid:quiz_id>/questions/add/', views.add_question, name='add_question'),
    path('quizzes/<uuid:quiz_id>/questions/<int:question_id>/edit/', views.edit_question, name='edit_question'),
    path('quizzes/<uuid:quiz_id>/questions/<int:question_id>/delete/', views.delete_question, name='delete_question'),
    
    # Category management
    path('categories/', views.manage_categories, name='manage_categories'),
    path('categories/create/', views.create_category, name='create_category'),
]
