from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Avg, Max
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from datetime import timedelta
import random
import string
from django import conf
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.contrib import messages


from .models import CustomUser, EmailVerificationOTP, UserActivity
from .forms import UserRegistrationForm, CustomLoginForm, UserProfileForm, EmailVerificationForm

# Import with error handling for models that might not exist yet
try:
    from quiz_app.models import UserQuizAttempt
except ImportError:
    UserQuizAttempt = None


# Check if Celery is properly configured
def can_use_celery():
    try:
        from celery import current_app
        # Try to inspect the celery app
        current_app.control.inspect().stats()
        return True
    except:
        return False

def send_verification_email_sync(user_id, otp):
    """Synchronous email sending function"""
    try:
        user = CustomUser.objects.get(id=user_id)
        print(f"Attempting to send email to: {user.email}")
        
        result = send_mail(
            subject='Verify Your Email - Quiz Platform',
            message=f'Your verification code is: {otp}\n\nThis code will expire in 10 minutes.',
            from_email='prathyunkumarreddy@gmail.com',  # Hardcoded for testing
            recipient_list=[user.email],
            fail_silently=False,
        )
        print(f"Email send result: {result}")
        return True
    except Exception as e:
        print(f"Email sending error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = 'registration/login.html'
    
    def get_success_url(self):
        return reverse_lazy('accounts:dashboard')
    
    def form_valid(self, form):
        """Handle successful login"""
        user = form.get_user()
        
        # Log activity (with error handling)
        try:
            UserActivity.objects.create(
                user=user,
                action='login',
                description='User logged in successfully',
                ip_address=self.request.META.get('REMOTE_ADDR'),
                user_agent=self.request.META.get('HTTP_USER_AGENT', '')
            )
        except Exception as e:
            print(f"Activity logging failed: {e}")
        
        messages.success(self.request, f'Welcome back, {user.display_name}!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """Handle failed login"""
        messages.error(self.request, 'Login failed. Please check your credentials.')
        return super().form_invalid(form)


class UserRegistrationView(CreateView):
    model = CustomUser
    form_class = UserRegistrationForm
    template_name = 'registration/register.html'
    success_url = reverse_lazy('accounts:verify_email')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Generate OTP
        otp = ''.join(random.choices(string.digits, k=6))
        
        # Create OTP with expiration time
        EmailVerificationOTP.objects.create(
            user=self.object, 
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send verification email (sync for now)
        email_sent = send_verification_email_sync(self.object.id, otp)
        
        if email_sent:
            messages.success(
                self.request, 
                f'Registration successful! Please check your email ({self.object.email}) for verification code.'
            )
        else:
            messages.warning(
                self.request,
                'Account created but email could not be sent. Please contact support or try resending.'
            )
        
        # Store user ID in session for verification
        self.request.session['verification_user_id'] = self.object.id
        
        return response

@login_required
def dashboard(request):
    # Get user statistics
    if UserQuizAttempt:
        user_stats = {
            'total_attempts': UserQuizAttempt.objects.filter(user=request.user).count(),
            'average_score': UserQuizAttempt.objects.filter(user=request.user).aggregate(
                avg_score=Avg('score')
            )['avg_score'] or 0,
            'best_score': UserQuizAttempt.objects.filter(user=request.user).aggregate(
                best_score=Max('score')
            )['best_score'] or 0,
        }
        
        # Recent quiz attempts
        recent_attempts = UserQuizAttempt.objects.filter(user=request.user).select_related('quiz').order_by('-started_at')[:5]
    else:
        user_stats = {
            'total_attempts': 0,
            'average_score': 0,
            'best_score': 0,
        }
        recent_attempts = []
    
    # Recent activities
    recent_activities = UserActivity.objects.filter(user=request.user).order_by('-timestamp')[:10]
    
    # Social stats - Fixed field names according to your Follow model
    
    
    context = {
        'user_stats': user_stats,
        'recent_attempts': recent_attempts,
        'recent_activities': recent_activities,
        
    }
    
    return render(request, 'accounts/dashboard.html', context)

def verify_email(request):
    user_id = request.session.get('verification_user_id')
    if not user_id:
        messages.error(request, 'Invalid verification session.')
        return redirect('accounts:login')
    
    user = get_object_or_404(CustomUser, id=user_id)
    
    if user.is_email_verified:
        messages.info(request, 'Email already verified.')
        return redirect('accounts:login')
    
    if request.method == 'POST':
        form = EmailVerificationForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data['otp']
            try:
                verification = EmailVerificationOTP.objects.get(
                    user=user,
                    otp=otp,
                    is_used=False
                )
                if verification.is_valid:
                    verification.is_used = True
                    verification.save()
                    
                    user.is_email_verified = True
                    user.save()
                    
                    # Log activity
                    UserActivity.objects.create(
                        user=user,
                        action='email_verified',
                        description='Email verified successfully',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    # Clear session
                    del request.session['verification_user_id']
                    
                    messages.success(request, 'Email verified successfully! You can now login.')
                    return redirect('accounts:login')
                else:
                    messages.error(request, 'OTP has expired. Please request a new one.')
            except EmailVerificationOTP.DoesNotExist:
                messages.error(request, 'Invalid OTP. Please try again.')
    else:
        form = EmailVerificationForm()
    
    context = {
        'form': form,
        'user': user,
    }
    return render(request, 'accounts/verify_email.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='profile_updated',
                description='Profile information updated',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('accounts:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    context = {
        'form': form,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def quiz_history(request):
    if UserQuizAttempt:
        attempts = UserQuizAttempt.objects.filter(user=request.user).select_related('quiz').order_by('-started_at')
        
        paginator = Paginator(attempts, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'attempts': page_obj.object_list,
        }
    else:
        context = {
            'page_obj': None,
            'attempts': [],
        }
    
    return render(request, 'accounts/quiz_history.html', context)

@login_required
def settings(request):
    if request.method == 'POST':
        # Handle settings update
        email_notifications = request.POST.get('email_notifications') == 'on'
        is_profile_public = request.POST.get('is_profile_public') == 'on'
        
        request.user.email_notifications = email_notifications
        request.user.is_profile_public = is_profile_public
        request.user.save()
        
        # Log activity
        UserActivity.objects.create(
            user=request.user,
            action='profile_updated',
            description='Settings updated',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')
        )
        
        messages.success(request, 'Settings updated successfully!')
        return redirect('accounts:settings')
    
    return render(request, 'accounts/settings.html')

@csrf_exempt
def resend_verification_email(request):
    if request.method == 'POST':
        user_id = request.session.get('verification_user_id')
        if not user_id:
            return JsonResponse({'success': False, 'message': 'Invalid session'})
        
        user = get_object_or_404(CustomUser, id=user_id)
        
        if user.is_email_verified:
            return JsonResponse({'success': False, 'message': 'Email already verified'})
        
        # Invalidate old OTPs
        EmailVerificationOTP.objects.filter(user=user, is_used=False).update(is_used=True)
        
        # Generate new OTP
        otp = ''.join(random.choices(string.digits, k=6))
        EmailVerificationOTP.objects.create(
            user=user, 
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )
        
        # Send verification email
        email_sent = send_verification_email_sync(user.id, otp)
        
        if email_sent:
            return JsonResponse({'success': True, 'message': 'Verification email sent!'})
        else:
            return JsonResponse({'success': False, 'message': 'Failed to send email'})
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def analytics(request):
    """User analytics view"""
    if UserQuizAttempt:
        # Quiz statistics
        quiz_stats = UserQuizAttempt.objects.filter(
            user=request.user, 
            status='completed'
        ).aggregate(
            total_quizzes=Count('id'),
            average_score=Avg('percentage_score'),
            best_score=Max('percentage_score'),
            total_score=Count('score')
        )
        
        # Monthly progress (last 6 months)
        monthly_data = []
        for i in range(6):
            month_start = timezone.now().replace(day=1) - timedelta(days=30*i)
            month_end = month_start + timedelta(days=30)
            
            month_attempts = UserQuizAttempt.objects.filter(
                user=request.user,
                status='completed',
                completed_at__gte=month_start,
                completed_at__lt=month_end
            )
            
            monthly_data.append({
                'month': month_start.strftime('%B'),
                'attempts': month_attempts.count(),
                'avg_score': month_attempts.aggregate(avg=Avg('percentage_score'))['avg'] or 0,
            })
        
        context = {
            'quiz_stats': quiz_stats,
            'monthly_data': reversed(monthly_data),
        }
    else:
        context = {
            'quiz_stats': {
                'total_quizzes': 0,
                'average_score': 0,
                'best_score': 0,
                'total_score': 0
            },
            'monthly_data': [],
        }
    
    return render(request, 'accounts/analytics.html', context)

# Logout view
class CustomLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Log activity before logout
            UserActivity.objects.create(
                user=request.user,
                action='logout',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
        return super().dispatch(request, *args, **kwargs)
