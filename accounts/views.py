from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import RegistrationForm, UserForm, ProfileForm
from .models import Profile, FriendRequest
from django.contrib.auth.models import User
from django.db.models import Q
from django.http import JsonResponse

def root_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return render(request, 'admin_dashboard.html')
        else:
            return render(request, 'dashboard.html')
    else:
        return render(request, 'landing.html')

def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('login')
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
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    friend_request, created = FriendRequest.objects.get_or_create(sender=request.user, receiver=user)
    
    context = {
        'profile_user': user,
        'friend_request_status': friend_request.status,
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
            return redirect('profile')
    else:
        user_form = UserForm(instance=request.user)
        profile_form = ProfileForm(instance=request.user.profile)
    return render(request, 'accounts/edit_profile.html', {'user_form': user_form, 'profile_form': profile_form})

@login_required
def user_search(request):
    return render(request, 'accounts/user_search.html')

@login_required
def api_user_search(request):
    query = request.GET.get('q')
    if query:
        users = User.objects.filter(Q(username__icontains=query) | Q(first_name__icontains=query) | Q(last_name__icontains=query)).exclude(username=request.user.username).exclude(is_superuser=True)
        data = {'users': list(users.values('username', 'first_name', 'last_name'))}
    else:
        data = {'users': []}
    return JsonResponse(data)

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
    if not to_user.is_superuser:
        FriendRequest.objects.get_or_create(sender=request.user, receiver=to_user)
    return redirect('view_profile', username=to_user_username)

@login_required
def accept_friend_request(request, from_user_username):
    from_user = get_object_or_404(User, username=from_user_username)
    friend_request = get_object_or_404(FriendRequest, sender=from_user, receiver=request.user)
    friend_request.status = 'accepted'
    friend_request.save()
    request.user.profile.friends.add(from_user)
    from_user.profile.friends.add(request.user)
    return redirect('friend_requests_list')

@login_required
def reject_friend_request(request, from_user_username):
    from_user = get_object_or_404(User, username=from_user_username)
    friend_request = get_object_or_404(FriendRequest, sender=from_user, receiver=request.user)
    friend_request.status = 'declined'
    friend_request.save()
    return redirect('friend_requests_list')

@login_required
def unfriend_user(request, username):
    user_to_unfriend = get_object_or_404(User, username=username)
    request.user.profile.friends.remove(user_to_unfriend)
    user_to_unfriend.profile.friends.remove(request.user)
    return redirect('view_profile', username=username)

@login_required
def block_user(request, username):
    user_to_block = get_object_or_404(User, username=username)
    request.user.profile.blocked_users.add(user_to_block)
    request.user.profile.friends.remove(user_to_block)
    user_to_block.profile.friends.remove(request.user)
    return redirect('view_profile', username=username)
