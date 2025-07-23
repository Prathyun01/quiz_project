from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count, Prefetch
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json

from .models import Follow, SocialNotification, UserProfile, QuizShare, Achievement, UserAchievement, SocialFeed
from .forms import UserProfileForm, QuizShareForm, SearchForm
from .services.discovery_service import DiscoveryService
from .services.follow_service import FollowService
from accounts.models import UserActivity

User = get_user_model()

@login_required
def discover_users(request):
    """Discover new users to follow"""
    # Get recommended users
    recommended_users = DiscoveryService.get_recommended_users(request.user, limit=12)
    
    # Get users by category filters
    filter_type = request.GET.get('filter', 'recommended')
    search_query = request.GET.get('search', '')
    
    if filter_type == 'popular':
        users = User.objects.annotate(
            followers_count=Count('followers')
        ).filter(
            is_active=True,
            is_email_verified=True
        ).exclude(id=request.user.id).order_by('-followers_count')
    
    elif filter_type == 'recent':
        users = User.objects.filter(
            is_active=True,
            is_email_verified=True
        ).exclude(id=request.user.id).order_by('-date_joined')
    
    elif filter_type == 'active':
        users = User.objects.filter(
            is_active=True,
            is_email_verified=True,
            last_activity__isnull=False
        ).exclude(id=request.user.id).order_by('-last_activity')
    
    else:  # recommended
        users = recommended_users
    
    # Apply search filter
    if search_query:
        users = users.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get follow status for current users
    following_ids = Follow.objects.filter(follower=request.user).values_list('followed_id', flat=True)
    
    context = {
        'page_obj': page_obj,
        'users': page_obj.object_list,
        'recommended_users': recommended_users[:6] if filter_type != 'recommended' else [],
        'filter_type': filter_type,
        'search_query': search_query,
        'following_ids': list(following_ids),
    }
    return render(request, 'social/discover_users.html', context)

@login_required
def user_profile(request, username):
    """Display user profile with social features"""
    profile_user = get_object_or_404(User, username=username, is_active=True)
    
    # Get or create social profile
    social_profile, created = UserProfile.objects.get_or_create(user=profile_user)
    
    # Check if current user follows this profile
    is_following = Follow.objects.filter(
        follower=request.user,
        followed=profile_user
    ).exists() if request.user != profile_user else False
    
    # Get follow counts
    followers_count = Follow.objects.filter(followed=profile_user).count()
    following_count = Follow.objects.filter(follower=profile_user).count()
    
    # Get recent quiz attempts (if allowed to view)
    recent_attempts = []
    if social_profile.show_quiz_history or request.user == profile_user:
        from quiz_app.models import UserQuizAttempt
        recent_attempts = UserQuizAttempt.objects.filter(
            user=profile_user,
            status='completed'
        ).select_related('quiz').order_by('-completed_at')[:10]
    
    # Get user achievements
    achievements = UserAchievement.objects.filter(
        user=profile_user,
        is_displayed=True
    ).select_related('achievement').order_by('-earned_at')[:6]
    
    # Get recent activity feed
    feed_activities = SocialFeed.objects.filter(
        user=profile_user,
        is_public=True
    ).order_by('-created_at')[:10]
    
    # Get mutual followers (if not viewing own profile)
    mutual_followers = []
    if request.user != profile_user:
        mutual_followers = User.objects.filter(
            followers__follower=request.user,
            following__followed=profile_user
        ).distinct()[:5]
    
    context = {
        'profile_user': profile_user,
        'social_profile': social_profile,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'recent_attempts': recent_attempts,
        'achievements': achievements,
        'feed_activities': feed_activities,
        'mutual_followers': mutual_followers,
        'is_own_profile': request.user == profile_user,
    }
    return render(request, 'social/user_profile.html', context)

@login_required
def edit_profile(request):
    """Edit social profile"""
    social_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=social_profile)
        if form.is_valid():
            form.save()
            
            # Log activity
            UserActivity.objects.create(
                user=request.user,
                action='profile_updated',
                description='Social profile updated'
            )
            
            messages.success(request, 'Profile updated successfully!')
            return redirect('social:user_profile', username=request.user.username)
    else:
        form = UserProfileForm(instance=social_profile)
    
    context = {
        'form': form,
        'social_profile': social_profile,
    }
    return render(request, 'social/edit_profile.html', context)

@csrf_exempt
@login_required
def follow_user(request):
    """Follow/unfollow a user via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        action = data.get('action')  # 'follow' or 'unfollow'
        
        target_user = User.objects.get(id=user_id)
        
        if target_user == request.user:
            return JsonResponse({'success': False, 'error': 'Cannot follow yourself'})
        
        if action == 'follow':
            follow_obj, created = Follow.objects.get_or_create(
                follower=request.user,
                followed=target_user
            )
            
            if created:
                # Send notification
                FollowService.send_follow_notification(request.user, target_user)
                
                # Create feed activity
                SocialFeed.objects.create(
                    user=request.user,
                    activity_type='user_followed',
                    title=f'Started following {target_user.display_name}',
                    description=f'{request.user.display_name} is now following {target_user.display_name}',
                    metadata={'followed_user_id': str(target_user.id)}
                )
                
                message = 'Successfully followed user'
            else:
                message = 'Already following this user'
        
        elif action == 'unfollow':
            deleted_count, _ = Follow.objects.filter(
                follower=request.user,
                followed=target_user
            ).delete()
            
            message = 'Successfully unfollowed user' if deleted_count > 0 else 'Not following this user'
        
        else:
            return JsonResponse({'success': False, 'error': 'Invalid action'})
        
        # Get updated counts
        followers_count = Follow.objects.filter(followed=target_user).count()
        following_count = Follow.objects.filter(follower=target_user).count()
        
        return JsonResponse({
            'success': True,
            'action': action,
            'message': message,
            'followers_count': followers_count,
            'following_count': following_count
        })
    
    except User.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'User not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def followers_list(request, username):
    """Display user's followers"""
    profile_user = get_object_or_404(User, username=username, is_active=True)
    social_profile, _ = UserProfile.objects.get_or_create(user=profile_user)
    
    # Check privacy settings
    if not social_profile.show_followers and request.user != profile_user:
        messages.error(request, 'This user has made their followers list private.')
        return redirect('social:user_profile', username=username)
    
    followers = Follow.objects.filter(followed=profile_user).select_related('follower').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(followers, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get mutual connections for current user
    mutual_connections = set()
    if request.user != profile_user:
        mutual_connections = set(
            Follow.objects.filter(
                follower=request.user,
                followed__in=[f.follower for f in page_obj.object_list]
            ).values_list('followed_id', flat=True)
        )
    
    context = {
        'profile_user': profile_user,
        'page_obj': page_obj,
        'followers': page_obj.object_list,
        'mutual_connections': mutual_connections,
        'title': f"{profile_user.display_name}'s Followers",
    }
    return render(request, 'social/followers_list.html', context)

@login_required
def following_list(request, username):
    """Display users that this user follows"""
    profile_user = get_object_or_404(User, username=username, is_active=True)
    social_profile, _ = UserProfile.objects.get_or_create(user=profile_user)
    
    # Check privacy settings
    if not social_profile.show_following and request.user != profile_user:
        messages.error(request, 'This user has made their following list private.')
        return redirect('social:user_profile', username=username)
    
    following = Follow.objects.filter(follower=profile_user).select_related('followed').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(following, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get mutual connections for current user
    mutual_connections = set()
    if request.user != profile_user:
        mutual_connections = set(
            Follow.objects.filter(
                follower=request.user,
                followed__in=[f.followed for f in page_obj.object_list]
            ).values_list('followed_id', flat=True)
        )
    
    context = {
        'profile_user': profile_user,
        'page_obj': page_obj,
        'following': page_obj.object_list,
        'mutual_connections': mutual_connections,
        'title': f"Users {profile_user.display_name} follows",
    }
    return render(request, 'social/following_list.html', context)

@login_required
def social_dashboard(request):
    """Social dashboard showing activity feed"""
    # Get followed users
    following_ids = Follow.objects.filter(follower=request.user).values_list('followed_id', flat=True)
    
    # Get activity feed from followed users and own activities
    feed_activities = SocialFeed.objects.filter(
        Q(user__in=following_ids) | Q(user=request.user),
        is_public=True
    ).select_related('user').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(feed_activities, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get suggested users
    suggested_users = DiscoveryService.get_recommended_users(request.user, limit=5)
    
    # Get recent notifications
    recent_notifications = SocialNotification.objects.filter(
        recipient=request.user
    ).order_by('-created_at')[:5]
    
    # Get user stats
    user_stats = {
        'followers': Follow.objects.filter(followed=request.user).count(),
        'following': Follow.objects.filter(follower=request.user).count(),
        'achievements': UserAchievement.objects.filter(user=request.user).count(),
        'unread_notifications': SocialNotification.objects.filter(
            recipient=request.user,
            is_read=False
        ).count()
    }
    
    context = {
        'page_obj': page_obj,
        'feed_activities': page_obj.object_list,
        'suggested_users': suggested_users,
        'recent_notifications': recent_notifications,
        'user_stats': user_stats,
    }
    return render(request, 'social/dashboard.html', context)

@login_required
def notifications(request):
    """Display user notifications"""
    notifications = SocialNotification.objects.filter(
        recipient=request.user
    ).select_related('sender').order_by('-created_at')
    
    # Filter by type if requested
    filter_type = request.GET.get('type')
    if filter_type:
        notifications = notifications.filter(notification_type=filter_type)
    
    # Mark all as read if requested
    if request.GET.get('mark_all_read'):
        notifications.filter(is_read=False).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('social:notifications')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'notifications': page_obj.object_list,
        'filter_type': filter_type,
    }
    return render(request, 'social/notifications.html', context)

@csrf_exempt
@login_required
def mark_notification_read(request):
    """Mark notification as read via AJAX"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid method'})
    
    try:
        data = json.loads(request.body)
        notification_id = data.get('notification_id')
        
        notification = SocialNotification.objects.get(
            id=notification_id,
            recipient=request.user
        )
        
        notification.mark_as_read()
        
        return JsonResponse({'success': True})
    
    except SocialNotification.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Notification not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def share_quiz(request, quiz_id):
    """Share a quiz with followers"""
    from quiz_app.models import Quiz
    
    quiz = get_object_or_404(Quiz, id=quiz_id, is_active=True, is_public=True)
    
    if request.method == 'POST':
        form = QuizShareForm(request.POST)
        if form.is_valid():
            quiz_share = form.save(commit=False)
            quiz_share.user = request.user
            quiz_share.quiz_id = str(quiz.id)
            quiz_share.quiz_title = quiz.title
            quiz_share.save()
            
            # Add selected users to share with
            if form.cleaned_data.get('shared_with'):
                quiz_share.shared_with.set(form.cleaned_data['shared_with'])
                
                # Send notifications
                for user in form.cleaned_data['shared_with']:
                    SocialNotification.objects.create(
                        recipient=user,
                        sender=request.user,
                        notification_type='quiz_shared',
                        title=f'{request.user.display_name} shared a quiz with you',
                        message=f'Check out "{quiz.title}" - {form.cleaned_data.get("share_message", "")}',
                        related_quiz_id=str(quiz.id),
                        related_url=f"/quiz/{quiz.id}/"
                    )
            
            # Create feed activity
            SocialFeed.objects.create(
                user=request.user,
                activity_type='quiz_shared',
                title=f'Shared quiz: {quiz.title}',
                description=form.cleaned_data.get('share_message', ''),
                metadata={'quiz_id': str(quiz.id), 'quiz_title': quiz.title},
                is_public=quiz_share.is_public
            )
            
            messages.success(request, 'Quiz shared successfully!')
            return redirect('quiz_app:quiz_detail', quiz_id=quiz.id)
    else:
        form = QuizShareForm()
        # Pre-populate with user's followers
        followers = User.objects.filter(
            following__follower=request.user
        ).order_by('first_name', 'last_name')
        form.fields['shared_with'].queryset = followers
    
    context = {
        'form': form,
        'quiz': quiz,
    }
    return render(request, 'social/share_quiz.html', context)

@login_required
def search_users(request):
    """Search for users"""
    form = SearchForm(request.GET or None)
    results = []
    
    if form and form.is_valid():
        query = form.cleaned_data['query']
        category = form.cleaned_data.get('category')
        
        results = DiscoveryService.search_users(
            query=query,
            category=category,
            exclude_user=request.user
        )
        
        # Pagination
        paginator = Paginator(results, 20)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
    else:
        page_obj = None
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'results': page_obj.object_list if page_obj else [],
    }
    return render(request, 'social/search_users.html', context)
