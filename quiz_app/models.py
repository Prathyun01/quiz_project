from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
import uuid

User = get_user_model()

class Category(models.Model):
    BUILTIN_CATEGORIES = [
        ('science', 'Science & Technology'),
        ('history', 'History'),
        ('geography', 'Geography'),
        ('literature', 'Literature'),
        ('mathematics', 'Mathematics'),
        ('sports', 'Sports'),
        ('entertainment', 'Entertainment'),
        ('business', 'Business'),
        ('health', 'Health & Medicine'),
        ('arts', 'Arts & Culture'),
        ('programming', 'Programming'),
        ('general', 'General Knowledge'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-question-circle')
    color = models.CharField(max_length=7, default='#007bff')
    is_active = models.BooleanField(default=True)
    is_builtin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Categories'

    def __str__(self):
        return self.name

    @property
    def quiz_count(self):
        return self.quiz_set.filter(is_active=True).count()

class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    AI_PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('perplexity', 'Perplexity AI'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    time_limit = models.IntegerField(help_text='Time limit in minutes', default=30)
    total_marks = models.IntegerField(default=100)
    pass_percentage = models.IntegerField(default=60, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_quizzes')
    ai_generated = models.BooleanField(default=True)  # Always True for user quizzes
    ai_provider = models.CharField(max_length=20, choices=AI_PROVIDER_CHOICES, default='gemini')
    ai_prompt = models.TextField(blank=True, help_text='Original prompt used for AI generation')
    featured_image = models.ImageField(upload_to='quiz_images/', blank=True, null=True)
    tags = models.CharField(max_length=500, blank=True, help_text='Comma-separated tags')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI Quiz'
        verbose_name_plural = 'AI Quizzes'

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.question_set.count()

    @property
    def attempt_count(self):
        return self.userquizattempt_set.count()

    @property
    def average_score(self):
        attempts = self.userquizattempt_set.filter(status='completed')
        if attempts:
            total = sum(attempt.score for attempt in attempts)
            return round(total / len(attempts), 2)
        return 0

class Question(models.Model):
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    explanation = models.TextField(blank=True, help_text='Explanation for the correct answer')
    marks = models.IntegerField(default=1)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quiz', 'order']
        unique_together = ['quiz', 'order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"

    @property
    def correct_choice(self):
        return self.choice_set.filter(is_correct=True).first()

class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['question', 'order']
        unique_together = ['question', 'order']

    def __str__(self):
        return f"{self.question.quiz.title} - Q{self.question.order} - Choice {self.order}"

class UserQuizAttempt(models.Model):
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField(default=0)
    time_taken = models.DurationField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"

    @property
    def incorrect_answers(self):
        """Calculate number of incorrect answers"""
        return self.total_questions - self.correct_answers

    @property
    def percentage_score(self):
        if self.quiz.total_marks > 0:
            return round((self.score / self.quiz.total_marks) * 100, 2)
        return 0

    @property
    def is_passed(self):
        return self.percentage_score >= self.quiz.pass_percentage

    @property
    def grade(self):
        percentage = self.percentage_score
        if percentage >= 90:
            return 'A+'
        elif percentage >= 80:
            return 'A'
        elif percentage >= 70:
            return 'B+'
        elif percentage >= 60:
            return 'B'
        elif percentage >= 50:
            return 'C'
        else:
            return 'F'


class UserAnswer(models.Model):
    attempt = models.ForeignKey(UserQuizAttempt, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(Choice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True, null=True)  # Add this field
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.user.username} - {self.question}"
