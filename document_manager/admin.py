from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Document, Tag, DocumentRating, DocumentDownload, DocumentFavorite

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'document_count_display', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'icon', 'color')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_count_display(self, obj):
        return obj.document_count
    document_count_display.short_description = 'Documents'

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'color', 'document_count_display', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']
    
    def document_count_display(self, obj):
        return obj.documents.count()
    document_count_display.short_description = 'Documents'

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'access_level', 'uploaded_by', 
        'file_size_display', 'download_count', 'view_count', 'is_active', 'created_at'
    ]
    list_filter = [
        'access_level', 'category', 'is_active', 'is_featured', 
        'created_at', 'uploaded_by'
    ]
    search_fields = ['title', 'description', 'uploaded_by__username']
    readonly_fields = [
        'id', 'file_size', 'download_count', 'view_count', 
        'created_at', 'updated_at', 'average_rating_display'
    ]
    filter_horizontal = ['tags']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Document Information', {
            'fields': ('title', 'description', 'category', 'tags')
        }),
        ('File Information', {
            'fields': ('file', 'thumbnail', 'file_size')
        }),
        ('Access Control', {
            'fields': ('access_level', 'uploaded_by')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Statistics', {
            'fields': ('download_count', 'view_count', 'average_rating_display'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def file_size_display(self, obj):
        return obj.formatted_file_size
    file_size_display.short_description = 'File Size'
    
    def average_rating_display(self, obj):
        avg_rating = obj.average_rating
        if avg_rating > 0:
            stars = '★' * int(avg_rating) + '☆' * (5 - int(avg_rating))
            return format_html(
                '<span title="{}/5">{} ({})</span>',
                avg_rating, stars, avg_rating
            )
        return 'No ratings'
    average_rating_display.short_description = 'Average Rating'

@admin.register(DocumentRating)
class DocumentRatingAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['document__title', 'user__username']
    readonly_fields = ['created_at']

@admin.register(DocumentDownload)
class DocumentDownloadAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'downloaded_at', 'ip_address']
    list_filter = ['downloaded_at']
    search_fields = ['document__title', 'user__username']
    readonly_fields = ['downloaded_at']
    date_hierarchy = 'downloaded_at'

@admin.register(DocumentFavorite)
class DocumentFavoriteAdmin(admin.ModelAdmin):
    list_display = ['document', 'user', 'created_at']
    list_filter = ['created_at']
    search_fields = ['document__title', 'user__username']
    readonly_fields = ['created_at']

# Customize admin site
admin.site.site_header = "Quiz Platform - Document Management"
admin.site.site_title = "Document Admin"
admin.site.index_title = "Welcome to Document Management"
