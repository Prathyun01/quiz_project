from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid

User = get_user_model()

class ManualQuizCategory(models.Model):
    """Categories for manually created quizzes"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, default='fas fa-folder')
    color = models.CharField(max_length=7, default='#6c757d')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ['name']
        verbose_name = 'Manual Quiz Category'
        verbose_name_plural = 'Manual Quiz Categories'

    def __str__(self):
        return self.name

    @property
    def quiz_count(self):
        return self.manualquiz_set.filter(is_active=True).count()

class ManualQuiz(models.Model):
    """Model for manually created quizzes by admin"""
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(ManualQuizCategory, on_delete=models.CASCADE, null=True, blank=True)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    time_limit = models.IntegerField(help_text='Time limit in minutes', default=30)
    total_marks = models.IntegerField(default=100)
    pass_percentage = models.IntegerField(default=60, validators=[MinValueValidator(0), MaxValueValidator(100)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_active = models.BooleanField(default=True)
    featured_image = models.ImageField(upload_to='manual_quiz_images/', blank=True, null=True)
    instructions = models.TextField(blank=True, help_text='Special instructions for quiz takers')
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='manual_quizzes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Manual Quiz'
        verbose_name_plural = 'Manual Quizzes'

    def __str__(self):
        return self.title

    @property
    def question_count(self):
        return self.manualquestion_set.count()

    @property
    def is_complete(self):
        return self.question_count > 0 and all(
            question.choice_count >= 2 for question in self.manualquestion_set.all()
        )

class ManualQuestion(models.Model):
    """Model for manually created questions"""
    QUESTION_TYPES = [
        ('multiple_choice', 'Multiple Choice'),
        ('true_false', 'True/False'),
        ('fill_blank', 'Fill in the Blank'),
        ('short_answer', 'Short Answer'),
    ]

    quiz = models.ForeignKey(ManualQuiz, on_delete=models.CASCADE)
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='multiple_choice')
    explanation = models.TextField(blank=True, help_text='Explanation for the correct answer')
    hints = models.TextField(blank=True, help_text='Hints to help quiz takers')
    marks = models.IntegerField(default=1, validators=[MinValueValidator(1)])
    order = models.IntegerField(default=0)
    is_required = models.BooleanField(default=True)
    image = models.ImageField(upload_to='question_images/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['quiz', 'order']
        unique_together = ['quiz', 'order']

    def __str__(self):
        return f"{self.quiz.title} - Q{self.order}"

    @property
    def choice_count(self):
        return self.manualchoice_set.count()

    @property
    def correct_choices(self):
        return self.manualchoice_set.filter(is_correct=True)

class ManualChoice(models.Model):
    """Model for manually created choices"""
    question = models.ForeignKey(ManualQuestion, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    explanation = models.TextField(blank=True, help_text='Explanation for this choice')

    class Meta:
        ordering = ['question', 'order']
        unique_together = ['question', 'order']

    def __str__(self):
        return f"{self.question.quiz.title} - Q{self.question.order} - Choice {self.order}"

class ManualQuizAttempt(models.Model):
    """Model for tracking attempts on manual quizzes"""
    STATUS_CHOICES = [
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    quiz = models.ForeignKey(ManualQuiz, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='in_progress')
    score = models.IntegerField(default=0)
    total_questions = models.IntegerField()
    correct_answers = models.IntegerField(default=0)
    time_taken = models.DurationField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']

    def __str__(self):
        return f"{self.user.username} - {self.quiz.title}"

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

class ManualQuizAnswer(models.Model):
    """Model for storing answers to manual quiz questions"""
    attempt = models.ForeignKey(ManualQuizAttempt, on_delete=models.CASCADE)
    question = models.ForeignKey(ManualQuestion, on_delete=models.CASCADE)
    selected_choice = models.ForeignKey(ManualChoice, on_delete=models.CASCADE, null=True, blank=True)
    text_answer = models.TextField(blank=True, help_text='For short answer questions')
    is_correct = models.BooleanField(default=False)
    marks_awarded = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['attempt', 'question']

    def __str__(self):
        return f"{self.attempt.user.username} - {self.question}"
