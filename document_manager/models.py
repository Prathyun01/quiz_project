from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.validators import FileExtensionValidator
from django.db.models import Avg
import uuid
import os

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-folder')
    color = models.CharField(max_length=7, default='#007bff')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('document_manager:category_documents', args=[self.pk])

    @property
    def document_count(self):
        return self.documents.filter(is_active=True).count()

class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    color = models.CharField(max_length=7, default='#6c757d')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

def document_upload_path(instance, filename):
    """Generate upload path for documents"""
    ext = filename.split('.')[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join('documents', str(instance.category.id), filename)

class Document(models.Model):
    ACCESS_CHOICES = [
        ('public', 'Public'),
        ('registered', 'Registered Users'),
        ('premium', 'Premium Users'),
        ('private', 'Private'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    file = models.FileField(
        upload_to=document_upload_path,
        validators=[FileExtensionValidator(
            allowed_extensions=['pdf', 'doc', 'docx', 'txt', 'ppt', 'pptx', 'xls', 'xlsx']
        )]
    )
    thumbnail = models.ImageField(upload_to='documents/thumbnails/', blank=True, null=True)
    
    # Metadata
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='documents')
    tags = models.ManyToManyField(Tag, blank=True, related_name='documents')
    
    # Access Control
    access_level = models.CharField(max_length=20, choices=ACCESS_CHOICES, default='public')
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_documents')
    
    # Statistics
    file_size = models.PositiveIntegerField(default=0, help_text="Size in bytes")
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('document_manager:document_detail', args=[self.pk])

    @property
    def file_extension(self):
        if self.file:
            return '.' + self.file.name.split('.')[-1].lower()
        return ''

    @property
    def formatted_file_size(self):
        """Return human readable file size"""
        if not self.file_size:
            return "Unknown"
        
        size = self.file_size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"

    def can_access(self, user=None):
        """Check if user can access this document"""
        if not self.is_active:
            return False
            
        if self.access_level == 'public':
            return True
        
        if not user or not user.is_authenticated:
            return False
        
        if self.access_level == 'registered':
            return True
        
        if self.access_level == 'premium':
            return getattr(user, 'is_premium', False) or user.is_staff
        
        if self.access_level == 'private':
            return user == self.uploaded_by or user.is_staff
        
        return False

    @property
    def average_rating(self):
        """Calculate average rating"""
        avg = self.ratings.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return round(avg, 1) if avg else 0

class DocumentRating(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(choices=[(i, i) for i in range(1, 6)])
    review = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['document', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.document.title} ({self.rating}/5)"

class DocumentDownload(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='document_downloads')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    class Meta:
        ordering = ['-downloaded_at']

    def __str__(self):
        return f"{self.user.username} downloaded {self.document.title}"

class DocumentFavorite(models.Model):
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='favorites')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorite_documents')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['document', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} favorited {self.document.title}"
