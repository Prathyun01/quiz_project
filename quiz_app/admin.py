from django.contrib import admin
from django.utils.html import format_html
from .models import Category, Quiz, Question, Choice, UserQuizAttempt, UserAnswer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_builtin', 'is_active', 'quiz_count', 'created_at']
    list_filter = ['is_builtin', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['quiz_count']

    def quiz_count(self, obj):
        return obj.quiz_count

class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 4
    max_num = 4

class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    inlines = [ChoiceInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'difficulty', 'ai_provider', 'created_by', 'question_count', 'is_active', 'created_at']
    list_filter = ['ai_generated', 'ai_provider', 'difficulty', 'is_active', 'is_public', 'created_at']
    search_fields = ['title', 'description', 'ai_prompt']
    readonly_fields = ['question_count', 'attempt_count', 'average_score']
    filter_horizontal = []
    inlines = [QuestionInline]

    def get_queryset(self, request):
        # Only show AI-generated quizzes in quiz_app admin
        return super().get_queryset(request).filter(ai_generated=True)

    def question_count(self, obj):
        return obj.question_count

    def attempt_count(self, obj):
        return obj.attempt_count

    def average_score(self, obj):
        return f"{obj.average_score}%"

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['quiz', 'question_text', 'question_type', 'marks', 'order']
    list_filter = ['question_type', 'quiz__category', 'quiz__difficulty']
    search_fields = ['question_text', 'quiz__title']
    inlines = [ChoiceInline]

@admin.register(UserQuizAttempt)
class UserQuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['user', 'quiz', 'status', 'score', 'percentage_score', 'grade', 'started_at']
    list_filter = ['status', 'quiz__difficulty', 'quiz__category', 'started_at']
    search_fields = ['user__username', 'quiz__title']
    readonly_fields = ['percentage_score', 'grade', 'is_passed']

    def percentage_score(self, obj):
        return f"{obj.percentage_score}%"

    def grade(self, obj):
        grade = obj.grade
        if grade in ['A+', 'A']:
            color = 'green'
        elif grade in ['B+', 'B']:
            color = 'blue'
        elif grade == 'C':
            color = 'orange'
        else:
            color = 'red'
        return format_html('<span style="color: {}; font-weight: bold;">{}</span>', color, grade)
