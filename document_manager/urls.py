from django.urls import path
from . import views

app_name = 'document_manager'

urlpatterns = [
    # Main views
    path('', views.document_list, name='document_list'),
    path('categories/', views.categories, name='categories'),
    path('category/<int:category_id>/', views.category_documents, name='category_documents'),
    path('search/', views.search_documents, name='search_documents'),
    
    # Document CRUD
    path('document/<uuid:document_id>/', views.document_detail, name='document_detail'),
    path('document/<uuid:document_id>/download/', views.download_document, name='download_document'),
    path('upload/', views.upload_document, name='upload_document'),
    path('my-documents/', views.my_documents, name='my_documents'),
    
    # AJAX endpoints
    path('rate/', views.rate_document, name='rate_document'),
    path('toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
]
