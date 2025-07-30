from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse, Http404
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import ListView
from django.conf import settings
import mimetypes
import os
import json

from .models import Document, Category, DocumentDownload, DocumentRating, DocumentFavorite, Tag
from .forms import DocumentUploadForm, DocumentRatingForm, DocumentSearchForm

def document_list(request):
    """Display paginated list of documents with filtering"""
    documents = Document.objects.filter(is_active=True).select_related('category', 'uploaded_by').prefetch_related('tags')
    categories = Category.objects.filter(is_active=True).annotate(doc_count=Count('documents'))
    
    # Search and filtering
    search_form = DocumentSearchForm(request.GET or None)
    if search_form.is_valid():
        query = search_form.cleaned_data.get('query')
        category = search_form.cleaned_data.get('category')
        access_level = search_form.cleaned_data.get('access_level')
        
        if query:
            documents = documents.filter(
                Q(title__icontains=query) |
                Q(description__icontains=query) |
                Q(tags__name__icontains=query)
            ).distinct()
        
        if category:
            documents = documents.filter(category=category)
        
        if access_level:
            documents = documents.filter(access_level=access_level)
    
    # Featured documents
    featured_docs = documents.filter(is_featured=True)[:3]
    
    # Pagination
    paginator = Paginator(documents.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'featured_docs': featured_docs,
        'search_form': search_form,
        'total_documents': documents.count(),
    }
    return render(request, 'document_manager/document_list.html', context)

def document_detail(request, document_id):
    """Display document details"""
    document = get_object_or_404(Document, id=document_id, is_active=True)
    
    # Update view count
    document.view_count += 1
    document.save(update_fields=['view_count'])
    
    # Check if user has favorited this document
    is_favorited = False
    user_rating = None
    
    if request.user.is_authenticated:
        is_favorited = DocumentFavorite.objects.filter(
            document=document, user=request.user
        ).exists()
        
        try:
            user_rating = DocumentRating.objects.get(document=document, user=request.user)
        except DocumentRating.DoesNotExist:
            pass
    
    # Get recent ratings
    recent_ratings = DocumentRating.objects.filter(
        document=document
    ).select_related('user').order_by('-created_at')[:5]
    
    # Related documents
    related_documents = Document.objects.filter(
        category=document.category,
        is_active=True
    ).exclude(id=document.id).select_related('uploaded_by')[:6]
    
    context = {
        'document': document,
        'user_rating': user_rating,
        'recent_ratings': recent_ratings,
        'related_documents': related_documents,
        'is_favorited': is_favorited,
    }
    return render(request, 'document_manager/document_detail.html', context)

def category_documents(request, category_id):
    """Display documents for a specific category"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    documents = Document.objects.filter(
        category=category,
        is_active=True
    ).select_related('uploaded_by').order_by('-created_at')
    
    # Search within category
    search_query = request.GET.get('search')
    if search_query:
        documents = documents.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(documents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'search_query': search_query,
    }
    return render(request, 'document_manager/category_documents.html', context)

def categories(request):
    """Display all categories"""
    categories = Category.objects.filter(is_active=True).annotate(
        document_count=Count('documents', filter=Q(documents__is_active=True))
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'document_manager/categories.html', context)

@login_required
def download_document(request, document_id):
    """Handle document download"""
    document = get_object_or_404(Document, id=document_id, is_active=True)
    
    # Check if user can download
    if not document.can_access(request.user):
        messages.error(request, 'You do not have permission to download this document.')
        return redirect('document_manager:document_detail', document_id=document.id)
    
    try:
        # Record download
        DocumentDownload.objects.create(
            document=document,
            user=request.user,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Update download count
        document.download_count += 1
        document.save(update_fields=['download_count'])
        
        # Serve file
        if document.file and os.path.exists(document.file.path):
            content_type, _ = mimetypes.guess_type(document.file.path)
            
            with open(document.file.path, 'rb') as f:
                response = HttpResponse(f.read(), content_type=content_type or 'application/octet-stream')
                filename = f"{document.title}{document.file_extension}"
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                return response
        else:
            messages.error(request, 'File not found.')
            return redirect('document_manager:document_detail', document_id=document.id)
    
    except Exception as e:
        messages.error(request, f'Error downloading file: {str(e)}')
        return redirect('document_manager:document_detail', document_id=document.id)

@login_required
def upload_document(request):
    """Upload new document"""
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            form.save_m2m()
            
            messages.success(request, f'Document "{document.title}" uploaded successfully!')
            return redirect('document_manager:document_detail', document_id=document.id)
    else:
        form = DocumentUploadForm()
    
    context = {
        'form': form,
    }
    return render(request, 'document_manager/upload_document.html', context)

@login_required
def my_documents(request):
    """Display user's uploaded documents"""
    documents = Document.objects.filter(
        uploaded_by=request.user
    ).select_related('category').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(documents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'document_manager/my_documents.html', context)

@csrf_exempt
@login_required
def rate_document(request):
    """Handle document rating via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            document_id = data.get('document_id')
            rating_value = int(data.get('rating'))
            review = data.get('review', '')
            
            if not (1 <= rating_value <= 5):
                return JsonResponse({'success': False, 'error': 'Invalid rating value'})
            
            document = get_object_or_404(Document, id=document_id, is_active=True)
            
            # Create or update rating
            rating, created = DocumentRating.objects.update_or_create(
                document=document,
                user=request.user,
                defaults={
                    'rating': rating_value,
                    'review': review
                }
            )
            
            # Calculate new average rating
            avg_rating = document.average_rating
            rating_count = document.ratings.count()
            
            return JsonResponse({
                'success': True,
                'message': 'Rating saved successfully!',
                'average_rating': avg_rating,
                'rating_count': rating_count,
                'user_rating': rating_value
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def toggle_favorite(request):
    """Toggle document favorite status"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            document_id = data.get('document_id')
            document = get_object_or_404(Document, id=document_id)
            
            favorite, created = DocumentFavorite.objects.get_or_create(
                document=document,
                user=request.user
            )
            
            if not created:
                favorite.delete()
                action = 'removed'
                message = 'Removed from favorites'
            else:
                action = 'added'
                message = 'Added to favorites'
            
            return JsonResponse({
                'success': True,
                'action': action,
                'message': message
            })
            
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def search_documents(request):
    """Search documents with advanced filters"""
    query = request.GET.get('q', '').strip()
    documents = Document.objects.filter(is_active=True)
    
    if query:
        documents = documents.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(tags__name__icontains=query)
        ).distinct()
    
    # Additional filters
    category_id = request.GET.get('category')
    if category_id:
        documents = documents.filter(category_id=category_id)
    
    access_level = request.GET.get('access_level')
    if access_level:
        documents = documents.filter(access_level=access_level)
    
    # Pagination
    paginator = Paginator(documents.order_by('-created_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'query': query,
        'categories': Category.objects.filter(is_active=True),
    }
    return render(request, 'document_manager/search_results.html', context)
