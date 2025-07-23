from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML
from .models import Category

class AIQuizGenerationForm(forms.Form):
    CATEGORY_CHOICES = [
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

    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    time_limit = forms.IntegerField(
        min_value=5,
        max_value=120,
        initial=30,
        widget=forms.NumberInput(attrs={'class': 'form-control'}),
        help_text='Time limit in minutes'
    )
    
    AI_PROVIDER_CHOICES = [
        ('gemini', 'Google Gemini'),
        ('perplexity', 'Perplexity AI'),
    ]

    topic = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the topic for quiz generation (e.g., Python Programming, World War II)'
        }),
        help_text='Be specific about the topic you want the quiz to cover'
    )

    category = forms.ChoiceField(
        choices=CATEGORY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Select the most appropriate category for your quiz'
    )

    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        initial='medium',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Choose the difficulty level appropriate for your audience'
    )

    num_questions = forms.IntegerField(
        min_value=5,
        max_value=20,
        initial=10,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '5',
            'max': '20'
        }),
        help_text='Number of questions to generate (5-20)'
    )

    ai_provider = forms.ChoiceField(
        choices=AI_PROVIDER_CHOICES,
        initial='gemini',
        widget=forms.Select(attrs={'class': 'form-control'}),
        help_text='Choose the AI service to generate your quiz'
    )


    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info"><i class="fas fa-robot"></i> Generate an AI-powered quiz on any topic!</div>'),
            Field('topic', css_class='form-group mb-3'),
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('difficulty', css_class='form-group col-md-6 mb-3'),
            ),
            Row(
                Column('num_questions', css_class='form-group col-md-4 mb-3'),
                Column('time_limit', css_class='form-group col-md-4 mb-3'),
                Column('ai_provider', css_class='form-group col-md-4 mb-3'),
            ),
            Submit('submit', 'Generate AI Quiz', css_class='btn btn-primary btn-lg')
        )

class QuizFilterForm(forms.Form):
    DIFFICULTY_CHOICES = [
        ('', 'All Difficulties'),
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    AI_PROVIDER_CHOICES = [
        ('', 'All Providers'),
        ('gemini', 'Google Gemini'),
        ('perplexity', 'Perplexity AI'),
    ]

    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search quizzes...'
        })
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    difficulty = forms.ChoiceField(
        choices=DIFFICULTY_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    ai_provider = forms.ChoiceField(
        choices=AI_PROVIDER_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
