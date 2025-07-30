from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.urls import reverse
from django.utils import timezone
from django.forms import modelformset_factory
import json

from .models import ManualQuiz, ManualQuestion, ManualChoice, ManualQuizCategory, ManualQuizAttempt
from .forms import ManualQuizForm, ManualQuestionForm, ManualChoiceForm, ManualQuizCategoryForm

def is_staff_or_superuser(user):
    """Check if user is staff or superuser"""
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_staff_or_superuser)
def admin_dashboard(request):
    """Admin dashboard for manual quiz management"""
    # Get statistics
    stats = {
        'total_quizzes': ManualQuiz.objects.filter(created_by=request.user).count(),
        'published_quizzes': ManualQuiz.objects.filter(created_by=request.user, status='published').count(),
        'draft_quizzes': ManualQuiz.objects.filter(created_by=request.user, status='draft').count(),
        'total_questions': ManualQuestion.objects.filter(quiz__created_by=request.user).count(),
        'total_attempts': ManualQuizAttempt.objects.filter(quiz__created_by=request.user).count(),
    }

    # Recent quizzes
    recent_quizzes = ManualQuiz.objects.filter(created_by=request.user).order_by('-updated_at')[:5]

    # Recent attempts
    recent_attempts = ManualQuizAttempt.objects.filter(
        quiz__created_by=request.user
    ).select_related('user', 'quiz').order_by('-started_at')[:10]

    context = {
        'stats': stats,
        'recent_quizzes': recent_quizzes,
        'recent_attempts': recent_attempts,
    }
    return render(request, 'admin_quiz/dashboard.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def quiz_list(request):
    """List all manual quizzes created by admin"""
    quizzes = ManualQuiz.objects.filter(created_by=request.user).select_related('category')
    
    # Filter by status
    status_filter = request.GET.get('status')
    if status_filter:
        quizzes = quizzes.filter(status=status_filter)

    # Search
    search_query = request.GET.get('search')
    if search_query:
        quizzes = quizzes.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )

    # Pagination
    paginator = Paginator(quizzes.order_by('-updated_at'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'quizzes': page_obj.object_list,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    return render(request, 'admin_quiz/quiz_list.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def create_quiz(request):
    """Create a new manual quiz"""
    if request.method == 'POST':
        form = ManualQuizForm(request.POST, request.FILES)
        if form.is_valid():
            quiz = form.save(commit=False)
            quiz.created_by = request.user
            quiz.save()
            messages.success(request, f'Quiz "{quiz.title}" created successfully!')
            return redirect('admin_quiz:quiz_detail', quiz_id=quiz.id)
    else:
        form = ManualQuizForm()

    context = {
        'form': form,
        'title': 'Create New Quiz',
    }
    return render(request, 'admin_quiz/create_quiz.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def quiz_detail(request, quiz_id):
    """View quiz details and manage questions"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    questions = quiz.manualquestion_set.all().prefetch_related('manualchoice_set')
    
    context = {
        'quiz': quiz,
        'questions': questions,
    }
    return render(request, 'admin_quiz/quiz_detail.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def edit_quiz(request, quiz_id):
    """Edit quiz details"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ManualQuizForm(request.POST, request.FILES, instance=quiz)
        if form.is_valid():
            quiz = form.save()
            messages.success(request, f'Quiz "{quiz.title}" updated successfully!')
            return redirect('admin_quiz:quiz_detail', quiz_id=quiz.id)
    else:
        form = ManualQuizForm(instance=quiz)

    context = {
        'form': form,
        'quiz': quiz,
        'title': f'Edit Quiz: {quiz.title}',
    }
    return render(request, 'admin_quiz/edit_quiz.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def add_question(request, quiz_id):
    """Add a question to a quiz"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    
    if request.method == 'POST':
        form = ManualQuestionForm(request.POST, request.FILES)
        if form.is_valid():
            question = form.save(commit=False)
            question.quiz = quiz
            if not question.order:
                question.order = quiz.manualquestion_set.count() + 1
            question.save()
            messages.success(request, 'Question added successfully!')
            return redirect('admin_quiz:edit_question', quiz_id=quiz.id, question_id=question.id)
    else:
        form = ManualQuestionForm(initial={'order': quiz.manualquestion_set.count() + 1})

    context = {
        'form': form,
        'quiz': quiz,
        'title': f'Add Question to {quiz.title}',
    }
    return render(request, 'admin_quiz/add_question.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def edit_question(request, quiz_id, question_id):
    """Edit a question and its choices"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    question = get_object_or_404(ManualQuestion, id=question_id, quiz=quiz)
    
    # Create formset for choices
    ChoiceFormSet = modelformset_factory(
        ManualChoice,
        fields=['choice_text', 'is_correct', 'order', 'explanation'],
        extra=2,
        can_delete=True
    )
    
    if request.method == 'POST':
        question_form = ManualQuestionForm(request.POST, request.FILES, instance=question)
        choice_formset = ChoiceFormSet(request.POST, queryset=question.manualchoice_set.all())
        
        if question_form.is_valid() and choice_formset.is_valid():
            question = question_form.save()
            
            # Save choices
            choices = choice_formset.save(commit=False)
            for choice in choices:
                choice.question = question
                choice.save()
            
            # Delete marked choices
            for obj in choice_formset.deleted_objects:
                obj.delete()
            
            messages.success(request, 'Question updated successfully!')
            return redirect('admin_quiz:quiz_detail', quiz_id=quiz.id)
    else:
        question_form = ManualQuestionForm(instance=question)
        choice_formset = ChoiceFormSet(queryset=question.manualchoice_set.all())

    context = {
        'question_form': question_form,
        'choice_formset': choice_formset,
        'quiz': quiz,
        'question': question,
        'title': f'Edit Question: {question.question_text[:50]}...',
    }
    return render(request, 'admin_quiz/edit_question.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def delete_question(request, quiz_id, question_id):
    """Delete a question"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    question = get_object_or_404(ManualQuestion, id=question_id, quiz=quiz)
    
    if request.method == 'POST':
        question.delete()
        messages.success(request, 'Question deleted successfully!')
        return redirect('admin_quiz:quiz_detail', quiz_id=quiz.id)
    
    context = {
        'quiz': quiz,
        'question': question,
    }
    return render(request, 'admin_quiz/delete_question.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def manage_categories(request):
    """Manage quiz categories"""
    categories = ManualQuizCategory.objects.filter(created_by=request.user).annotate(
        quiz_count=Count('manualquiz')
    ).order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'admin_quiz/manage_categories.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def create_category(request):
    """Create a new category"""
    if request.method == 'POST':
        form = ManualQuizCategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            messages.success(request, f'Category "{category.name}" created successfully!')
            return redirect('admin_quiz:manage_categories')
    else:
        form = ManualQuizCategoryForm()

    context = {
        'form': form,
        'title': 'Create New Category',
    }
    return render(request, 'admin_quiz/create_category.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def quiz_analytics(request, quiz_id):
    """View quiz analytics"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    attempts = ManualQuizAttempt.objects.filter(quiz=quiz, status='completed')
    
    analytics_data = {
        'total_attempts': attempts.count(),
        'average_score': sum(a.percentage_score for a in attempts) / len(attempts) if attempts else 0,
        'pass_rate': len([a for a in attempts if a.is_passed]) / len(attempts) * 100 if attempts else 0,
        'recent_attempts': attempts.order_by('-completed_at')[:10],
    }

    context = {
        'quiz': quiz,
        'analytics': analytics_data,
    }
    return render(request, 'admin_quiz/quiz_analytics.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def preview_quiz(request, quiz_id):
    """Preview quiz as it would appear to users"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    questions = quiz.manualquestion_set.all().prefetch_related('manualchoice_set')
    
    context = {
        'quiz': quiz,
        'questions': questions,
        'is_preview': True,
    }
    return render(request, 'admin_quiz/preview_quiz.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def publish_quiz(request, quiz_id):
    """Publish or unpublish a quiz"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    
    if not quiz.is_complete:
        messages.error(request, 'Cannot publish incomplete quiz. Please add questions and choices.')
        return redirect('admin_quiz:quiz_detail', quiz_id=quiz.id)
    
    if quiz.status == 'published':
        quiz.status = 'draft'
        messages.success(request, f'Quiz "{quiz.title}" unpublished.')
    else:
        quiz.status = 'published'
        messages.success(request, f'Quiz "{quiz.title}" published successfully!')
    
    quiz.save()
    return redirect('admin_quiz:quiz_detail', quiz_id=quiz.id)

@login_required
@user_passes_test(is_staff_or_superuser)
def delete_quiz(request, quiz_id):
    """Delete a quiz"""
    quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    
    if request.method == 'POST':
        quiz_title = quiz.title
        quiz.delete()
        messages.success(request, f'Quiz "{quiz_title}" deleted successfully!')
        return redirect('admin_quiz:quiz_list')
    
    context = {
        'quiz': quiz,
    }
    return render(request, 'admin_quiz/delete_quiz.html', context)

@login_required
@user_passes_test(is_staff_or_superuser)
def duplicate_quiz(request, quiz_id):
    """Duplicate an existing quiz"""
    original_quiz = get_object_or_404(ManualQuiz, id=quiz_id, created_by=request.user)
    
    # Create duplicate quiz
    new_quiz = ManualQuiz.objects.create(
        title=f"{original_quiz.title} (Copy)",
        description=original_quiz.description,
        category=original_quiz.category,
        difficulty=original_quiz.difficulty,
        time_limit=original_quiz.time_limit,
        total_marks=original_quiz.total_marks,
        pass_percentage=original_quiz.pass_percentage,
        instructions=original_quiz.instructions,
        status='draft',
        created_by=request.user
    )
    
    # Duplicate questions and choices
    for question in original_quiz.manualquestion_set.all():
        new_question = ManualQuestion.objects.create(
            quiz=new_quiz,
            question_text=question.question_text,
            question_type=question.question_type,
            explanation=question.explanation,
            hints=question.hints,
            marks=question.marks,
            order=question.order,
            is_required=question.is_required
        )
        
        # Duplicate choices
        for choice in question.manualchoice_set.all():
            ManualChoice.objects.create(
                question=new_question,
                choice_text=choice.choice_text,
                is_correct=choice.is_correct,
                order=choice.order,
                explanation=choice.explanation
            )
    
    messages.success(request, f'Quiz duplicated as "{new_quiz.title}"!')
    return redirect('admin_quiz:quiz_detail', quiz_id=new_quiz.id)
