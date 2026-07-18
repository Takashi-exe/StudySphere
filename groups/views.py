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
from accounts.models import create_notification, Notification
from django.urls import reverse
import uuid

@login_required
def group_list(request):
    groups = request.user.study_groups.all().select_related('created_by')
    group_invitations = Notification.objects.filter(recipient=request.user, notif_type='group_invite', is_read=False)
    context = {
        'groups': groups,
        'group_invitations': group_invitations,
    }
    return render(request, 'groups/group_list.html', context)

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
    group = get_object_or_404(StudyGroup, id=group_id)
    
    if request.method == 'POST' and 'content' in request.POST:
        content = request.POST.get('content')
        if content:
            GroupChatMessage.objects.create(group=group, user=request.user, content=content)
            return redirect('groups:group_detail', group_id=group.id)

    active_session_prefetch = Prefetch('sessions', queryset=StudySession.objects.filter(is_active=True).prefetch_related('participants__profile'), to_attr='active_sessions_list')
    group_with_active_session = StudyGroup.objects.prefetch_related(active_session_prefetch).get(id=group_id)
    active_session = group_with_active_session.active_sessions_list[0] if group_with_active_session.active_sessions_list else None

    past_group_sessions = StudySession.objects.filter(group=group, is_active=False).order_by('-start_time')[:2]
    
    memberships = GroupMembership.objects.filter(group=group).select_related('user', 'user__profile').order_by('joined_at')
    user_membership = memberships.filter(user=request.user).first()
    
    is_member = user_membership is not None
    is_admin = is_member and user_membership.role == 'admin'
    is_moderator = is_member and user_membership.role == 'moderator'

    context = {
        'group': group,
        'chat_messages': group.chat_messages.all().select_related('user__profile'),
        'past_sessions': past_group_sessions,
        'active_session': active_session,
        'has_active_session': active_session is not None,
        'is_member': is_member,
        'is_admin': is_admin,
        'is_moderator': is_moderator,
        'memberships': memberships,
    }
    return render(request, 'groups/group_detail.html', context)

@require_POST
@login_required
def remove_member(request, group_id, user_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    requesting_membership = get_object_or_404(GroupMembership, group=group, user=request.user)
    target_membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)

    if not (requesting_membership.role == 'admin' or requesting_membership.role == 'moderator'):
        return HttpResponseForbidden("You do not have permission to remove members.")
    if requesting_membership.role == 'moderator' and target_membership.role != 'member':
        messages.error(request, "Moderators can only remove regular members.")
        return redirect('groups:group_detail', group_id=group.id)
    if target_membership.user == group.created_by:
        messages.error(request, "The group creator cannot be removed.")
        return redirect('groups:group_detail', group_id=group.id)
    
    target_membership.delete()
    messages.success(request, f"{target_membership.user.username} has been removed from the group.")
    return redirect('groups:group_detail', group_id=group.id)

@require_POST
@login_required
def promote_member(request, group_id, user_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.user != group.created_by:
        return HttpResponseForbidden("Only the group creator can promote members.")
    
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    if membership.role == 'member':
        membership.role = 'moderator'
        membership.save()
        messages.success(request, f"{membership.user.username} has been promoted to moderator.")
    return redirect('groups:group_detail', group_id=group.id)

@require_POST
@login_required
def demote_member(request, group_id, user_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.user != group.created_by:
        return HttpResponseForbidden("Only the group creator can demote members.")
    
    membership = get_object_or_404(GroupMembership, group=group, user_id=user_id)
    if membership.role == 'moderator':
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
    
    GroupMembership.objects.filter(group=group, user=request.user).delete()
    messages.success(request, f"You have left the group '{group.name}'.")
    return redirect('groups:group_list')

@login_required
def group_settings(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    membership = get_object_or_404(GroupMembership, user=request.user, group=group)
    is_admin = membership.role == 'admin'

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'edit_info' and is_admin:
            group.name = request.POST.get('name', group.name).strip()
            group.description = request.POST.get('description', group.description).strip()
            if 'cover_image' in request.FILES:
                group.cover_image = request.FILES['cover_image']
            group.is_private = request.POST.get('is_private') == 'on'
            group.save()
            messages.success(request, 'Group settings updated.')
            return redirect('groups:group_settings', group_id=group.id)
        elif action == 'delete_group' and is_admin:
            group_name = group.name
            group.delete()
            messages.success(request, f'"{group_name}" has been deleted.')
            return redirect('groups:group_list')
        elif action == 'regenerate_invite' and is_admin:
            group.invite_code = uuid.uuid4()
            group.save()
            messages.success(request, 'Invite code regenerated.')
            return redirect('groups:group_settings', group_id=group.id)
        elif action == 'leave_group' and not is_admin:
            membership.delete()
            messages.success(request, f'You have left "{group.name}".')
            return redirect('groups:group_list')

    return render(request, 'groups/group_settings.html', {
        'group': group,
        'is_admin': is_admin,
        'membership': membership,
        'member_count': group.members.count(),
    })

@login_required
def join_group(request, invite_code):
    group = get_object_or_404(StudyGroup, invite_code=invite_code)
    if not group.members.filter(id=request.user.id).exists():
        GroupMembership.objects.create(user=request.user, group=group)
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
    return JsonResponse({'success': True, 'username': target_user.username})