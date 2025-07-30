from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
import json
import uuid
from .models import Quiz, Category, Question, UserQuizAttempt, UserAnswer, Choice
from .forms import AIQuizGenerationForm, QuizFilterForm
from .services.ai_service import AIQuizService

def quiz_list(request):
    """Display paginated list of AI-generated quizzes with filtering options"""
    quizzes = Quiz.objects.filter(is_active=True, is_public=True, ai_generated=True).select_related('category', 'created_by')
    
    form = QuizFilterForm(request.GET)
    
    # Apply filters
    if form.is_valid():
        if form.cleaned_data.get('category'):
            quizzes = quizzes.filter(category=form.cleaned_data['category'])
        
        if form.cleaned_data.get('difficulty'):
            quizzes = quizzes.filter(difficulty=form.cleaned_data['difficulty'])
        
        if form.cleaned_data.get('search'):
            search_query = form.cleaned_data['search']
            quizzes = quizzes.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(tags__icontains=search_query)
            )
        
        if form.cleaned_data.get('ai_provider'):
            quizzes = quizzes.filter(ai_provider=form.cleaned_data['ai_provider'])
    
    # Pagination
    paginator = Paginator(quizzes.order_by('-created_at'), 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter - FIXED: renamed annotated field
    categories = Category.objects.filter(is_active=True).annotate(
        total_ai_quizzes=Count('quiz', filter=Q(quiz__ai_generated=True))
    ).order_by('name')
    
    context = {
        'page_obj': page_obj,
        'quizzes': page_obj.object_list,
        'form': form,
        'categories': categories,
        'total_quizzes': quizzes.count(),
    }
    
    return render(request, 'quiz_app/quiz_list.html', context)

def categories(request):
    """Display quiz categories with built-in categories highlighted"""
    # FIXED: Removed annotation that was causing the conflict
    categories = Category.objects.filter(is_active=True).order_by('-is_builtin', 'name')
    
    # Calculate total quizzes for stats
    total_active_quizzes = Quiz.objects.filter(
        is_active=True, 
        is_public=True, 
        ai_generated=True
    ).count()
    
    context = {
        'categories': categories,
        'total_active_quizzes': total_active_quizzes,
    }
    
    return render(request, 'quiz_app/categories.html', context)

def category_quizzes(request, category_id):
    """Display AI quizzes for a specific category"""
    category = get_object_or_404(Category, id=category_id, is_active=True)
    
    quizzes = Quiz.objects.filter(
        category=category,
        is_active=True,
        is_public=True,
        ai_generated=True
    ).select_related('created_by').order_by('-created_at')
    
    paginator = Paginator(quizzes, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
        'quizzes': page_obj.object_list,
    }
    
    return render(request, 'quiz_app/category_quizzes.html', context)

@login_required
def generate_ai_quiz(request):
    """Generate AI quiz using selected provider"""
    if request.method == 'POST':
        form = AIQuizGenerationForm(request.POST)
        if form.is_valid():
            try:
                # Get form data
                topic = form.cleaned_data['topic']
                category_choice = form.cleaned_data['category']  # This is the slug from form
                difficulty = form.cleaned_data['difficulty']
                num_questions = form.cleaned_data['num_questions']
                ai_provider = form.cleaned_data['ai_provider']
                
                # Get category name from the form choices
                category_name = dict(form.fields['category'].choices)[category_choice]
                
                # Get or create category using the slug
                category, created = Category.objects.get_or_create(
                    slug=category_choice,  # Use the category choice as slug
                    defaults={
                        'name': category_name,
                        'is_builtin': True,
                        'is_active': True,
                        'description': f'Quizzes related to {category_name}'
                    }
                )
                
                # Generate quiz using AI service
                ai_service = AIQuizService()
                quiz_data = ai_service.generate_quiz(
                    topic=topic,
                    category=category_name,
                    difficulty=difficulty,
                    num_questions=num_questions,
                    provider=ai_provider
                )
                
                # Create quiz in database
                quiz = Quiz.objects.create(
                    title=quiz_data.get('title', f'{topic} Quiz'),
                    description=quiz_data.get('description', f'AI generated quiz about {topic}'),
                    category=category,
                    difficulty=difficulty,
                    time_limit=30,  # Default 30 minutes
                    total_marks=num_questions * 1,  # 1 mark per question
                    created_by=request.user,
                    ai_provider=ai_provider,
                    ai_prompt=topic,
                    ai_generated=True
                )
                
                # Create questions and choices
                for idx, question_data in enumerate(quiz_data.get('questions', []), 1):
                    question = Question.objects.create(
                        quiz=quiz,
                        question_text=question_data['question'],
                        question_type='multiple_choice',
                        explanation=question_data.get('explanation', ''),
                        marks=1,
                        order=idx
                    )
                    
                    # Create choices
                    for choice_idx, choice_text in enumerate(question_data['choices'], 1):
                        Choice.objects.create(
                            question=question,
                            choice_text=choice_text,
                            is_correct=(choice_idx == question_data['correct_answer']),
                            order=choice_idx
                        )
                
                messages.success(request, f'AI quiz "{quiz.title}" generated successfully!')
                return redirect('quiz_app:quiz_detail', quiz_id=quiz.id)
                
            except Exception as e:
                messages.error(request, f'Error generating AI quiz: {str(e)}')
                return render(request, 'quiz_app/generate_ai_quiz.html', {'form': form})
    else:
        form = AIQuizGenerationForm()
    
    context = {
        'form': form,
        'available_providers': AIQuizService().get_available_providers()
    }
    
    return render(request, 'quiz_app/generate_ai_quiz.html', context)


def quiz_detail(request, quiz_id):
    """Display detailed quiz information"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True, is_public=True)

    # Get user's previous attempts
    user_attempts = []
    if request.user.is_authenticated:
        user_attempts = UserQuizAttempt.objects.filter(
            user=request.user, quiz=quiz
        ).order_by('-started_at')[:5]

    # Get related quizzes
    related_quizzes = Quiz.objects.filter(
        category=quiz.category,
        is_active=True,
        is_public=True,
        ai_generated=True
    ).exclude(id=quiz.id)[:6]

    context = {
        'quiz': quiz,
        'user_attempts': user_attempts,
        'related_quizzes': related_quizzes,
        'questions': quiz.question_set.all(),
    }
    return render(request, 'quiz_app/quiz_detail.html', context)

@login_required
def take_quiz(request, quiz_id):
    """Handle quiz taking process"""
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True, is_public=True)

    # Check if user has an ongoing attempt
    ongoing_attempt = UserQuizAttempt.objects.filter(
        user=request.user,
        quiz=quiz,
        status='in_progress'
    ).first()

    if request.method == 'POST':
        # Handle quiz submission
        attempt_id = request.POST.get('attempt_id')
        attempt = get_object_or_404(UserQuizAttempt, id=attempt_id, user=request.user)
        
        questions = quiz.question_set.all()
        correct_answers = 0
        total_marks = 0

        for question in questions:
            answer_key = f'question_{question.id}'
            user_answer = request.POST.get(answer_key)
            
            if user_answer:
                # Use get_or_create to avoid duplicate creation
                user_answer_obj, created = UserAnswer.objects.get_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'text_answer': '',
                        'is_correct': False,
                        'marks_awarded': 0
                    }
                )

                # Check answer and award marks
                if question.question_type == 'multiple_choice':
                    try:
                        selected_choice = question.choice_set.get(id=int(user_answer))
                        user_answer_obj.selected_choice = selected_choice
                        
                        if selected_choice.is_correct:
                            user_answer_obj.is_correct = True
                            user_answer_obj.marks_awarded = question.marks
                            correct_answers += 1
                            total_marks += question.marks
                        else:
                            user_answer_obj.is_correct = False
                            user_answer_obj.marks_awarded = 0
                            
                        user_answer_obj.save()
                        
                    except (ValueError, TypeError, Choice.DoesNotExist):
                        pass
                elif question.question_type == 'true_false':
                    # Handle true/false questions
                    is_correct = (user_answer.lower() == 'true' and 
                                question.choice_set.filter(is_correct=True, choice_text__icontains='true').exists()) or \
                               (user_answer.lower() == 'false' and 
                                question.choice_set.filter(is_correct=True, choice_text__icontains='false').exists())
                    
                    user_answer_obj.text_answer = user_answer
                    user_answer_obj.is_correct = is_correct
                    user_answer_obj.marks_awarded = question.marks if is_correct else 0
                    user_answer_obj.save()
                    
                    if is_correct:
                        correct_answers += 1
                        total_marks += question.marks

        # Complete the attempt
        attempt.status = 'completed'
        attempt.completed_at = timezone.now()
        attempt.score = total_marks
        attempt.correct_answers = correct_answers
        attempt.time_taken = attempt.completed_at - attempt.started_at
        attempt.save()

        return redirect('quiz_app:quiz_results', quiz_id=quiz.id, attempt_id=attempt.id)

    # Start new attempt or continue existing
    if not ongoing_attempt:
        ongoing_attempt = UserQuizAttempt.objects.create(
            user=request.user,
            quiz=quiz,
            total_questions=quiz.question_count,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )

    questions = quiz.question_set.all().prefetch_related('choice_set')

    context = {
        'quiz': quiz,
        'questions': questions,
        'attempt': ongoing_attempt,
        'time_limit_seconds': quiz.time_limit * 60,
    }
    return render(request, 'quiz_app/take_quiz.html', context)


@login_required
def quiz_results(request, quiz_id, attempt_id):
    """Display quiz results"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    attempt = get_object_or_404(UserQuizAttempt, id=attempt_id, user=request.user, quiz=quiz)

    # Get user answers with questions and correct choices
    user_answers = UserAnswer.objects.filter(attempt=attempt).select_related(
        'question', 'selected_choice'
    ).prefetch_related('question__choice_set')

    context = {
        'attempt': attempt,
        'quiz': quiz,
        'user_answers': user_answers,
        'total_questions': attempt.total_questions,
        'percentage': attempt.percentage_score,
    }
    return render(request, 'quiz_app/quiz_results.html', context)

@login_required
def quiz_dashboard(request):
    """Quiz dashboard for authenticated users"""
    # User's recent attempts
    recent_attempts = UserQuizAttempt.objects.filter(user=request.user).select_related(
        'quiz'
    ).order_by('-started_at')[:10]

    # User's statistics
    stats = {
        'total_attempts': UserQuizAttempt.objects.filter(user=request.user).count(),
        'completed_attempts': UserQuizAttempt.objects.filter(user=request.user, status='completed').count(),
        'average_score': 0,
        'best_score': 0,
    }

    completed_attempts = UserQuizAttempt.objects.filter(user=request.user, status='completed')
    if completed_attempts.exists():
        stats['average_score'] = sum(a.score for a in completed_attempts) / len(completed_attempts)
        stats['best_score'] = max(a.score for a in completed_attempts)

    # Recommended quizzes
    recommended_quizzes = Quiz.objects.filter(
        is_active=True,
        is_public=True,
        ai_generated=True
    ).exclude(
        id__in=UserQuizAttempt.objects.filter(user=request.user).values_list('quiz', flat=True)
    ).order_by('-created_at')[:6]

    context = {
        'recent_attempts': recent_attempts,
        'stats': stats,
        'recommended_quizzes': recommended_quizzes,
    }
    return render(request, 'quiz_app/dashboard.html', context)

@csrf_exempt
@login_required
def ajax_save_answer(request):
    """AJAX endpoint to save quiz answers in real-time"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attempt_id = data.get('attempt_id')
            question_id = data.get('question_id')
            answer_data = data.get('answer')

            attempt = UserQuizAttempt.objects.get(id=attempt_id, user=request.user)
            question = Question.objects.get(id=question_id, quiz=attempt.quiz)

            # Save or update user answer
            user_answer, created = UserAnswer.objects.get_or_create(
                attempt=attempt,
                question=question
            )

            if question.question_type == 'multiple_choice':
                try:
                    choice = Choice.objects.get(id=int(answer_data), question=question)
                    user_answer.selected_choice = choice
                    user_answer.is_correct = choice.is_correct
                    user_answer.marks_awarded = question.marks if choice.is_correct else 0
                except (ValueError, Choice.DoesNotExist):
                    pass

            user_answer.save()
            return JsonResponse({'success': True})

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@csrf_exempt
@login_required
def ajax_submit_quiz(request):
    """AJAX endpoint to submit quiz"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            attempt_id = data.get('attempt_id')
            attempt = UserQuizAttempt.objects.get(id=attempt_id, user=request.user)

            # Calculate final score
            user_answers = UserAnswer.objects.filter(attempt=attempt)
            total_marks = sum(answer.marks_awarded for answer in user_answers)
            correct_answers = user_answers.filter(is_correct=True).count()

            # Complete the attempt
            attempt.status = 'completed'
            attempt.completed_at = timezone.now()
            attempt.score = total_marks
            attempt.correct_answers = correct_answers
            attempt.time_taken = attempt.completed_at - attempt.started_at
            attempt.save()

            return JsonResponse({
                'success': True,
                'redirect_url': reverse('quiz_app:quiz_results', kwargs={
                    'quiz_id': attempt.quiz.id,
                    'attempt_id': attempt.id
                })
            })

        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid request method'})

def leaderboard(request):
    """Display leaderboard of top performers"""
    top_performers = UserQuizAttempt.objects.filter(
        status='completed'
    ).select_related('user', 'quiz').order_by('-percentage_score')[:20]

    context = {
        'top_performers': top_performers,
    }
    return render(request, 'quiz_app/leaderboard.html', context)

def quiz_analytics(request, quiz_id):
    """Display analytics for a specific quiz"""
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    # Only creator or admin can view analytics
    if not (request.user == quiz.created_by or request.user.is_staff):
        messages.error(request, 'You do not have permission to view analytics for this quiz.')
        return redirect('quiz_app:quiz_detail', quiz_id=quiz.id)

    attempts = UserQuizAttempt.objects.filter(quiz=quiz, status='completed')
    
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
    return render(request, 'quiz_app/quiz_analytics.html', context)
