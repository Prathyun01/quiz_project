from django.urls import path, include
from rest_framework.routers import DefaultRouter

# API Router (temporarily disabled but ready for future use)
router = DefaultRouter()

# Future API endpoints can be registered here
# router.register(r'quizzes', QuizViewSet)
# router.register(r'users', UserViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls')),
]
