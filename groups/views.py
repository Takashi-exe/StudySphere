from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudyGroup, GroupMembership, GroupChatMessage, GroupResource
from .forms import GroupForm, GroupResourceForm
from studySessions.models import StudySession
from django.db.models import Prefetch
from django.http import HttpResponseForbidden, JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from accounts.models import create_notification
from django.urls import reverse

@login_required
def group_list(request):
    groups = request.user.study_groups.all().select_related('created_by')
    return render(request, 'groups/group_list.html', {'groups': groups})

@login_required
def create_group(request):
    if request.method == 'POST':
        form = GroupForm(request.POST, request.FILES)
        if form.is_valid():
            group = form.save(commit=False)
            group.created_by = request.user
            group.save()
            GroupMembership.objects.create(user=request.user, group=group, role='admin')
            messages.success(request, f"Group '{group.name}' created successfully.")
            return redirect('groups:group_detail', group_id=group.id)
    else:
        form = GroupForm()
    return render(request, 'groups/group_form.html', {'form': form})

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(
        StudyGroup.objects.prefetch_related(
            'chat_messages__user__profile', 
            'resources__uploaded_by__profile'
        ), 
        id=group_id
    )
    
    if request.method == 'POST' and 'content' in request.POST:
        content = request.POST.get('content')
        if content:
            GroupChatMessage.objects.create(group=group, user=request.user, content=content)
            return redirect('groups:group_detail', group_id=group.id)

    active_session_prefetch = Prefetch(
        'sessions',
        queryset=StudySession.objects.filter(is_active=True).prefetch_related('participants__profile'),
        to_attr='active_sessions_list'
    )
    group_with_active_session = StudyGroup.objects.prefetch_related(active_session_prefetch).get(id=group_id)
    active_session = group_with_active_session.active_sessions_list[0] if group_with_active_session.active_sessions_list else None

    past_group_sessions = StudySession.objects.filter(group=group, is_active=False).order_by('-start_time')[:2]
    user_study_history = StudySession.objects.filter(participants=request.user, is_active=False).order_by('-start_time')[:5]

    memberships = GroupMembership.objects.filter(group=group).select_related('user', 'user__profile').order_by('joined_at')
    is_member = request.user.id in [m.user_id for m in memberships]
    
    is_admin = False
    if is_member:
        for m in memberships:
            if m.user_id == request.user.id and m.role == 'admin':
                is_admin = True
                break
    
    resource_form = GroupResourceForm()

    context = {
        'group': group,
        'chat_messages': group.chat_messages.all(),
        'past_sessions': past_group_sessions,
        'user_study_history': user_study_history,
        'active_session': active_session,
        'has_active_session': active_session is not None,
        'is_member': is_member,
        'is_admin': is_admin,
        'memberships': memberships,
        'resource_form': resource_form,
    }
    return render(request, 'groups/group_detail.html', context)

@login_required
def upload_resource(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.method == 'POST':
        form = GroupResourceForm(request.POST, request.FILES)
        if form.is_valid():
            resource = form.save(commit=False)
            resource.group = group
            resource.uploaded_by = request.user
            resource.save()
            messages.success(request, 'Resource uploaded successfully.')
    return redirect('groups:group_detail', group_id=group.id)


@login_required
def join_group(request, invite_code):
    group = get_object_or_404(StudyGroup, invite_code=invite_code)
    if not group.members.filter(id=request.user.id).exists():
        GroupMembership.objects.create(user=request.user, group=group)
        admins = GroupMembership.objects.filter(group=group, role='admin').select_related('user')
        for admin_membership in admins:
            if admin_membership.user != request.user:
                create_notification(
                    recipient=admin_membership.user,
                    notif_type='group_invite',
                    message=f"{request.user.username} joined your group '{group.name}'.",
                    link=reverse('groups:group_detail', args=[group.id]),
                    sender=request.user,
                )
        messages.success(request, f"You have successfully joined the group '{group.name}'.")
    else:
        messages.info(request, f"You are already a member of the group '{group.name}'.")
    return redirect('groups:group_detail', group_id=group.id)

@require_POST
@login_required
def add_member(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    is_admin = GroupMembership.objects.filter(user=request.user, group=group, role='admin').exists()
    if not is_admin:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    username = request.POST.get('username', '').strip()
    target_user = get_object_or_404(User, username=username)

    if group.members.filter(id=target_user.id).exists():
        return JsonResponse({'error': 'Already a member'}, status=400)
    
    GroupMembership.objects.create(user=target_user, group=group, role='member')
    create_notification(
        recipient=target_user,
        notif_type='group_invite',
        message=f"You were added to the group '{group.name}' by {request.user.username}.",
        link=reverse('groups:group_detail', args=[group.id]),
        sender=request.user,
    )
    return JsonResponse({'success': True, 'username': target_user.username})

@require_POST
@login_required
def remove_member(request, group_id, user_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    
    if not GroupMembership.objects.filter(user=request.user, group=group, role='admin').exists():
        return HttpResponseForbidden("You do not have permission to remove members.")
    if str(group.created_by_id) == str(user_id):
        messages.error(request, "The group creator cannot be removed.")
        return redirect('groups:group_detail', group_id=group.id)
    if request.user.id == int(user_id):
        messages.error(request, "You cannot remove yourself.")
        return redirect('groups:group_detail', group_id=group.id)
    
    membership.delete()
    messages.success(request, f"{membership.user.username} has been removed from the group.")
    return redirect('groups:group_detail', group_id=group.id)

@require_POST
@login_required
def promote_member(request, group_id, user_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.user != group.created_by:
        return HttpResponseForbidden("Only the group creator can promote members.")
    
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    membership.role = 'admin'
    membership.save()
    messages.success(request, f"{membership.user.username} has been promoted to admin.")
    return redirect('groups:group_detail', group_id=group.id)

@require_POST
@login_required
def demote_member(request, group_id, user_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.user != group.created_by:
        return HttpResponseForbidden("Only the group creator can demote members.")
    if int(user_id) == group.created_by_id:
        return HttpResponseForbidden("The group creator cannot be demoted.")
        
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    membership.role = 'member'
    membership.save()
    messages.success(request, f"{membership.user.username} has been demoted to member.")
    return redirect('groups:group_detail', group_id=group.id)

@require_POST
@login_required
def leave_group(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.user == group.created_by:
        messages.error(request, "Group creators cannot leave the group. You can delete it instead.")
        return redirect('groups:group_detail', group_id=group.id)
    
    membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    membership.delete()
    messages.success(request, f"You have left the group '{group.name}'.")
    return redirect('groups:group_list')