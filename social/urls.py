from django.urls import path
from . import views

app_name = 'social'

urlpatterns = [
    # Main social views
    path('', views.social_dashboard, name='dashboard'),
    path('discover/', views.discover_users, name='discover_users'),
    path('search/', views.search_users, name='search_users'),
    
    # Profile views
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    
    # Follow system
    path('users/<str:username>/followers/', views.followers_list, name='followers_list'),
    path('users/<str:username>/following/', views.following_list, name='following_list'),
    
    # Quiz sharing
    path('share-quiz/<uuid:quiz_id>/', views.share_quiz, name='share_quiz'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
    
    # AJAX endpoints
    path('ajax/follow-user/', views.follow_user, name='follow_user'),
    path('ajax/mark-notification-read/', views.mark_notification_read, name='mark_notification_read'),
]
