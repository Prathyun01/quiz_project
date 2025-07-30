from django.contrib import admin
from django.utils.html import format_html
from .models import ManualQuizCategory, ManualQuiz, ManualQuestion, ManualChoice, ManualQuizAttempt

@admin.register(ManualQuizCategory)
class ManualQuizCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'quiz_count', 'is_active', 'created_by', 'created_at']
    list_filter = ['is_active', 'created_at', 'created_by']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['quiz_count']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

class ManualChoiceInline(admin.TabularInline):
    model = ManualChoice
    extra = 4
    fields = ['choice_text', 'is_correct', 'order', 'explanation']

class ManualQuestionInline(admin.StackedInline):
    model = ManualQuestion
    extra = 1
    fields = ['question_text', 'question_type', 'explanation', 'hints', 'marks', 'order', 'is_required', 'image']

@admin.register(ManualQuiz)
class ManualQuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'status', 'question_count', 'is_complete', 'created_by', 'created_at']
    list_filter = ['status', 'difficulty', 'is_active', 'created_at', 'category']
    search_fields = ['title', 'description']
    readonly_fields = ['question_count', 'is_complete']
    inlines = [ManualQuestionInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'featured_image')
        }),
        ('Quiz Settings', {
            'fields': ('difficulty', 'time_limit', 'total_marks', 'pass_percentage', 'instructions')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'is_active')
        }),
        ('Metadata', {
            'fields': ('question_count', 'is_complete'),
            'classes': ('collapse',)
        })
    )

    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    def is_complete(self, obj):
        if obj.is_complete:
            return format_html('<span style="color: green;">✓ Complete</span>')
        else:
            return format_html('<span style="color: red;">✗ Incomplete</span>')
    is_complete.short_description = 'Completion Status'

@admin.register(ManualQuestion)
class ManualQuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'question_text_short', 'question_type', 'marks', 'order', 'choice_count']
    list_filter = ['question_type', 'quiz__category', 'quiz__difficulty', 'is_required']
    search_fields = ['question_text', 'quiz__title']
    inlines = [ManualChoiceInline]
    
    fieldsets = (
        ('Question Content', {
            'fields': ('quiz', 'question_text', 'question_type', 'image')
        }),
        ('Settings', {
            'fields': ('marks', 'order', 'is_required')
        }),
        ('Help & Explanation', {
            'fields': ('hints', 'explanation'),
            'classes': ('collapse',)
        })
    )

    def question_text_short(self, obj):
        return obj.question_text[:50] + "..." if len(obj.question_text) > 50 else obj.question_text
    question_text_short.short_description = 'Question'

    def choice_count(self, obj):
        return obj.choice_count
    choice_count.short_description = 'Choices'

@admin.register(ManualQuizAttempt)
class ManualQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'status', 'score', 'percentage_score', 'grade', 'started_at']
    list_filter = ['status', 'quiz__difficulty', 'quiz__category', 'started_at']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['percentage_score', 'grade', 'is_passed']

    def percentage_score(self, obj):
        return f"{obj.percentage_score}%"

    def grade(self, obj):
        grade = obj.grade
        colors = {
            'A+': 'green', 'A': 'green', 'B+': 'blue', 'B': 'blue',
            'C': 'orange', 'F': 'red'
        }
        color = colors.get(grade, 'black')
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, grade)
