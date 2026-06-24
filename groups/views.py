from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import StudyGroup, GroupMembership, GroupChatMessage
from studySessions.models import StudySession

@login_required
def group_list(request):
    groups = request.user.study_groups.all().select_related('created_by')
    return render(request, 'groups/group_list.html', {'groups': groups})

@login_required
def create_group(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        is_private = request.POST.get('is_private') == 'on'
        
        group = StudyGroup.objects.create(
            name=name,
            description=description,
            is_private=is_private,
            created_by=request.user
        )
        GroupMembership.objects.create(user=request.user, group=group, role='admin')
        messages.success(request, f"Group '{name}' created successfully.")
        return redirect('groups:group_detail', group_id=group.id)
        
    return render(request, 'groups/group_form.html')

@login_required
def group_detail(request, group_id):
    group = get_object_or_404(StudyGroup.objects.prefetch_related('members', 'chat_messages__user__profile'), id=group_id)
    
    if request.method == 'POST':
        content = request.POST.get('content')
        if content:
            GroupChatMessage.objects.create(group=group, user=request.user, content=content)
            return redirect('groups:group_detail', group_id=group.id)

    past_sessions = StudySession.objects.filter(group=group, is_active=False).order_by('-start_time')
    is_member = group.members.filter(id=request.user.id).exists()
    is_admin = is_member and GroupMembership.objects.filter(user=request.user, group=group, role='admin').exists()

    context = {
        'group': group,
        'chat_messages': group.chat_messages.all(),
        'past_sessions': past_sessions,
        'is_member': is_member,
        'is_admin': is_admin,
    }
    return render(request, 'groups/group_detail.html', context)

@login_required
def join_group(request, invite_code):
    group = get_object_or_404(StudyGroup, invite_code=invite_code)
    if not group.members.filter(id=request.user.id).exists():
        GroupMembership.objects.create(user=request.user, group=group)
        messages.success(request, f"You have successfully joined the group '{group.name}'.")
    else:
        messages.info(request, f"You are already a member of the group '{group.name}'.")
    return redirect('groups:group_detail', group_id=group.id)