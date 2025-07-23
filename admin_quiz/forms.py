from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field, HTML, Fieldset
from .models import ManualQuiz, ManualQuestion, ManualChoice, ManualQuizCategory

class ManualQuizForm(forms.ModelForm):
    class Meta:
        model = ManualQuiz
        fields = ['title', 'description', 'category', 'difficulty', 'time_limit', 
                 'total_marks', 'pass_percentage', 'featured_image', 'instructions', 'status']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter quiz title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe your quiz'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'difficulty': forms.Select(attrs={'class': 'form-control'}),
            'time_limit': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 180}),
            'total_marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'pass_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info"><i class="fas fa-info-circle"></i> Create a manual quiz with custom questions.</div>'),
            Fieldset(
                'Basic Information',
                Field('title', css_class='form-group mb-3'),
                Field('description', css_class='form-group mb-3'),
                Row(
                    Column('category', css_class='form-group col-md-6 mb-3'),
                    Column('difficulty', css_class='form-group col-md-6 mb-3'),
                ),
                Field('featured_image', css_class='form-group mb-3'),
            ),
            Fieldset(
                'Quiz Settings',
                Row(
                    Column('time_limit', css_class='form-group col-md-4 mb-3'),
                    Column('total_marks', css_class='form-group col-md-4 mb-3'),
                    Column('pass_percentage', css_class='form-group col-md-4 mb-3'),
                ),
                Field('instructions', css_class='form-group mb-3'),
                Field('status', css_class='form-group mb-3'),
            ),
            Submit('submit', 'Create Quiz', css_class='btn btn-primary btn-lg')
        )

class ManualQuestionForm(forms.ModelForm):
    class Meta:
        model = ManualQuestion
        fields = ['question_text', 'question_type', 'explanation', 'hints', 'marks', 'order', 'is_required', 'image']
        widgets = {
            'question_text': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter your question'}),
            'question_type': forms.Select(attrs={'class': 'form-control'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Explain the correct answer'}),
            'hints': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional hints for quiz takers'}),
            'marks': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('question_text', css_class='form-group mb-3'),
            Row(
                Column('question_type', css_class='form-group col-md-6 mb-3'),
                Column('marks', css_class='form-group col-md-3 mb-3'),
                Column('order', css_class='form-group col-md-3 mb-3'),
            ),
            Field('image', css_class='form-group mb-3'),
            Field('explanation', css_class='form-group mb-3'),
            Field('hints', css_class='form-group mb-3'),
            Field('is_required', css_class='form-check mb-3'),
            Submit('submit', 'Save Question', css_class='btn btn-success')
        )

class ManualChoiceForm(forms.ModelForm):
    class Meta:
        model = ManualChoice
        fields = ['choice_text', 'is_correct', 'order', 'explanation']
        widgets = {
            'choice_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter choice text'}),
            'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Optional explanation'}),
            'order': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

class ManualQuizCategoryForm(forms.ModelForm):
    class Meta:
        model = ManualQuizCategory
        fields = ['name', 'slug', 'description', 'icon', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
            'slug': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'category-slug'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'icon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'fas fa-folder'}),
            'color': forms.TextInput(attrs={'class': 'form-control', 'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('name', css_class='form-group mb-3'),
            Field('slug', css_class='form-group mb-3'),
            Field('description', css_class='form-group mb-3'),
            Row(
                Column('icon', css_class='form-group col-md-6 mb-3'),
                Column('color', css_class='form-group col-md-6 mb-3'),
            ),
            Submit('submit', 'Create Category', css_class='btn btn-primary')
        )

# Formsets for dynamic question and choice creation
from django.forms import formset_factory, modelformset_factory

ManualChoiceFormSet = modelformset_factory(
    ManualChoice,
    fields=['choice_text', 'is_correct', 'order', 'explanation'],
    extra=4,
    can_delete=True,
    widgets={
        'choice_text': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Choice text'}),
        'explanation': forms.Textarea(attrs={'class': 'form-control', 'rows': 1}),
        'order': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)
