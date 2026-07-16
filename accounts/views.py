from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm, UserForm, ProfileForm
from .models import Profile, FriendRequest, Notification, create_notification
from django.contrib.auth.models import User
from django.db.models import Q, Prefetch
from django.http import JsonResponse
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from groups.models import StudyGroup
from django.views.decorators.http import require_POST
from django.urls import reverse

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('root')
    else:
        form = AuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    return redirect('root')

@login_required
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(
            User.objects.prefetch_related(
                'profile',
                Prefetch('study_groups', queryset=StudyGroup.objects.prefetch_related('members__profile'))
            ),
            username=username
        )
    else:
        profile_user = request.user

    friendship_status = 'none'
    if request.user.is_authenticated and request.user != profile_user:
        if profile_user in request.user.profile.friends.all():
            friendship_status = 'friends'
        elif profile_user in request.user.profile.blocked_users.all():
            friendship_status = 'blocked_by_you'
        elif request.user in profile_user.profile.blocked_users.all():
            friendship_status = 'blocked_by_them'
        else:
            request_sent = FriendRequest.objects.filter(sender=request.user, receiver=profile_user, status='pending').exists()
            request_received = FriendRequest.objects.filter(sender=profile_user, receiver=request.user, status='pending').exists()
            if request_sent:
                friendship_status = 'sent'
            elif request_received:
                friendship_status = 'received'

    context = {
        'profile_user': profile_user,
        'friendship_status': friendship_status,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile_view(request):
    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        profile_form = ProfileForm(request.POST, request.FILES, instance=request.user.profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('accounts:profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'accounts/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})

@login_required
def user_search(request):
    return render(request, 'accounts/user_search.html')

@login_required
def api_user_search(request):
    query = request.GET.get('q', '')
    page_number = request.GET.get('page', 1)
    
    if not query:
        return JsonResponse({'users': [], 'has_next': False, 'total_results': 0})

    user_list = User.objects.filter(
        Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)
    ).exclude(username=request.user.username).exclude(is_superuser=True).select_related('profile').prefetch_related('study_groups')

    paginator = Paginator(user_list, 8) # 8 results per page
    page_obj = paginator.get_page(page_number)

    current_user_friends = request.user.profile.friends.all()
    sent_requests = FriendRequest.objects.filter(sender=request.user, status='pending').values_list('receiver_id', flat=True)
    current_user_groups = request.user.study_groups.all()

    data = []
    for user in page_obj:
        friendship_status = 'none'
        if user in current_user_friends:
            friendship_status = 'friends'
        elif user.id in sent_requests:
            friendship_status = 'sent'

        common_groups = user.study_groups.filter(id__in=current_user_groups.values_list('id', flat=True))

        data.append({
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'avatar': user.profile.avatar.url if user.profile.avatar else f"https://ui-avatars.com/api/?name={user.username.replace(' ', '+')}&background=random",
            'friendship_status': friendship_status,
            'common_groups': list(common_groups.values_list('name', flat=True)[:2]) # Limit to 2
        })

    return JsonResponse({
        'users': data,
        'has_next': page_obj.has_next(),
        'total_results': paginator.count
    })


@login_required
def friends_list(request):
    friends = request.user.profile.friends.exclude(id=request.user.id).exclude(is_superuser=True)
    return render(request, 'accounts/friends_list.html', {'friends': friends})

@login_required
def friend_requests_list(request):
    friend_requests = FriendRequest.objects.filter(receiver=request.user, status='pending')
    return render(request, 'accounts/friend_requests.html', {'friend_requests': friend_requests})

@login_required
def send_friend_request(request, to_user_username):
    to_user = get_object_or_404(User, username=to_user_username)

    if to_user == request.user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return redirect('accounts:view_profile', username=to_user_username)

    if to_user in request.user.profile.blocked_users.all() or request.user in to_user.profile.blocked_users.all():
        messages.error(request, "Cannot send friend request to a blocked user.")
        return redirect('accounts:view_profile', username=to_user_username)

    pending_request = FriendRequest.objects.filter(sender=to_user, receiver=request.user, status='pending').first()
    if pending_request:
        return accept_friend_request(request, to_user.username)

    friend_request, created = FriendRequest.objects.get_or_create(
        sender=request.user, 
        receiver=to_user,
        defaults={'status': 'pending'}
    )

    if not created and friend_request.status == 'declined':
        friend_request.status = 'pending'
        friend_request.created_at = timezone.now()
        friend_request.save()
        messages.success(request, "Friend request sent again.")
        create_notification(
            recipient=to_user,
            notif_type='friend_request',
            message=f"{request.user.username} sent you a friend request.",
            link=reverse('accounts:view_profile', args=[request.user.username]),
            sender=request.user,
        )
    elif created:
        messages.success(request, "Friend request sent.")
        create_notification(
            recipient=to_user,
            notif_type='friend_request',
            message=f"{request.user.username} sent you a friend request.",
            link=reverse('accounts:view_profile', args=[request.user.username]),
            sender=request.user,
        )
    else:
        messages.info(request, "Friend request already pending.")

    return redirect('accounts:view_profile', username=to_user_username)

@login_required
def accept_friend_request(request, from_user_username):
    from_user = get_object_or_404(User, username=from_user_username)

    if from_user == request.user:
        messages.error(request, "You cannot accept a friend request from yourself.")
        return redirect('accounts:friend_requests_list')

    friend_request = get_object_or_404(FriendRequest, sender=from_user, receiver=request.user, status='pending')
    
    friend_request.status = 'accepted'
    friend_request.save()
    
    request.user.profile.friends.add(from_user)
    from_user.profile.friends.add(request.user)
    
    FriendRequest.objects.filter(sender=request.user, receiver=from_user).delete()
    
    create_notification(
        recipient=from_user,
        notif_type='friend_request',
        message=f"{request.user.username} accepted your friend request.",
        link=reverse('accounts:view_profile', args=[request.user.username]),
        sender=request.user,
    )
    
    messages.success(request, f"You are now friends with {from_user.username}.")
    return redirect('accounts:friend_requests_list')

@login_required
def reject_friend_request(request, from_user_username):
    from_user = get_object_or_404(User, username=from_user_username)
    friend_request = get_object_or_404(FriendRequest, sender=from_user, receiver=request.user, status='pending')
    friend_request.status = 'declined'
    friend_request.save()
    messages.info(request, "Friend request declined.")
    return redirect('accounts:friend_requests_list')

@login_required
def unfriend_user(request, username):
    user_to_unfriend = get_object_or_404(User, username=username)
    
    request.user.profile.friends.remove(user_to_unfriend)
    user_to_unfriend.profile.friends.remove(request.user)
    
    FriendRequest.objects.filter(
        (Q(sender=request.user, receiver=user_to_unfriend) | Q(sender=user_to_unfriend, receiver=request.user))
    ).update(status='declined')
    
    messages.info(request, f"You are no longer friends with {user_to_unfriend.username}.")
    return redirect('accounts:view_profile', username=username)

@login_required
def block_user(request, username):
    user_to_block = get_object_or_404(User, username=username)

    if user_to_block == request.user:
        messages.error(request, "You cannot block yourself.")
        return redirect('accounts:view_profile', username=username)

    request.user.profile.blocked_users.add(user_to_block)
    
    request.user.profile.friends.remove(user_to_block)
    user_to_block.profile.friends.remove(request.user)
    
    FriendRequest.objects.filter(
        (Q(sender=request.user, receiver=user_to_block) | Q(sender=user_to_block, receiver=request.user))
    ).delete()
    
    messages.success(request, f"{user_to_block.username} has been blocked.")
    return redirect('accounts:view_profile', username=username)

@login_required
def notifications_view(request):
    notifications = Notification.objects.filter(recipient=request.user)
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'accounts/notifications.html', {'page_obj': page_obj})

@login_required
def notification_click(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, recipient=request.user)
    notif.is_read = True
    notif.save()
    if notif.link:
        return redirect(notif.link)
    return redirect('accounts:notifications')

@login_required
def notifications_unread_count(request):
    count = Notification.objects.filter(recipient=request.user, is_read=False).count()
    return JsonResponse({'count': count})

@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'success': True})