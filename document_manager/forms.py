from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Field, Row, Column, HTML
from .models import Document, Category, DocumentRating, Tag

class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = ['title', 'description', 'file', 'category', 'tags', 'access_level', 'thumbnail']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter document title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe the document...'}),
            'file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.ppt,.pptx,.xls,.xlsx'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'access_level': forms.Select(attrs={'class': 'form-control'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_enctype = 'multipart/form-data'
        self.helper.layout = Layout(
            HTML('<h4 class="text-glass mb-4">Document Information</h4>'),
            Field('title', css_class='form-group mb-3'),
            Field('description', css_class='form-group mb-3'),
            Row(
                Column('category', css_class='form-group col-md-6 mb-3'),
                Column('access_level', css_class='form-group col-md-6 mb-3'),
            ),
            Field('tags', css_class='form-group mb-3'),
            HTML('<h4 class="text-glass mb-4 mt-4">File Upload</h4>'),
            Field('file', css_class='form-group mb-3'),
            Field('thumbnail', css_class='form-group mb-3'),
            Submit('submit', 'Upload Document', css_class='btn btn-3d btn-lg w-100')
        )

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 50 * 1024 * 1024:  # 50MB limit
                raise forms.ValidationError('File size cannot exceed 50MB.')
        return file

class DocumentRatingForm(forms.ModelForm):
    class Meta:
        model = DocumentRating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(
                choices=[(i, f'{i} Star{"s" if i != 1 else ""}') for i in range(1, 6)], 
                attrs={'class': 'form-control'}
            ),
            'review': forms.Textarea(attrs={
                'class': 'form-control', 
                'rows': 3, 
                'placeholder': 'Write your review...'
            })
        }

class DocumentSearchForm(forms.Form):
    query = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search documents...',
        }),
        label='Search'
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Category'
    )
    access_level = forms.ChoiceField(
        choices=[('', 'All Access Levels')] + Document.ACCESS_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Access Level'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='col-md-4'),
                Column('category', css_class='col-md-3'),
                Column('access_level', css_class='col-md-3'),
                Column(Submit('submit', 'Search', css_class='btn btn-3d'), css_class='col-md-2 d-flex align-items-end'),
            )
        )
