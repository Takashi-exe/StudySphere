from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from groups.models import StudyGroup
from .models import StudySession, SessionPost, PostComment, SessionResource
from .forms import StudySessionForm, SessionPostForm, SessionResourceForm
from django.db.models import Count
from accounts.models import create_notification
from django.urls import reverse
from .summary import generate_session_summary
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import threading
import time

def broadcast_timer_updates():
    while True:
        for session in StudySession.objects.filter(is_active=True):
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'session_{session.id}',
                {
                    'type': 'timer_update',
                    'remaining_seconds': session.remaining_seconds,
                }
            )
        time.sleep(1)

# Start the timer broadcast thread
timer_thread = threading.Thread(target=broadcast_timer_updates)
timer_thread.daemon = True
timer_thread.start()

@login_required
def study_sessions_view(request):
    return render(request, 'studySessions/study_sessions.html')

@login_required
def start_session(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if request.method == 'POST':
        form = StudySessionForm(request.POST)
        if form.is_valid():
            session = form.save(commit=False)
            session.group = group
            session.created_by = request.user
            session.save()
            session.participants.add(*group.members.all())
            
            members = group.members.exclude(id=request.user.id)
            for member in members:
                create_notification(
                    recipient=member,
                    notif_type='session_start',
                    message=f"{request.user.username} started a session '{session.title}' in {group.name}.",
                    link=reverse('study_sessions:session_detail', args=[session.id]),
                    sender=request.user,
                )
            
            return redirect('study_sessions:session_detail', session_id=session.id)
    else:
        form = StudySessionForm()
    
    preset_durations = [25, 45, 60, 90]
    context = {
        'form': form,
        'group': group,
        'preset_durations': preset_durations
    }
    return render(request, 'studySessions/start_session.html', context)

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(
        StudySession.objects.prefetch_related(
            'posts__author__profile', 
            'participants__profile',
            'resources__uploaded_by'
        ), 
        id=session_id
    )
    
    can_post = session.is_active and request.user in session.participants.all()

    if request.method == 'POST':
        if not can_post:
            return HttpResponseForbidden("This session has ended and is read-only.")
        
        if 'content' in request.POST: # Handle chat post
            form = SessionPostForm(request.POST)
            if form.is_valid():
                post = form.save(commit=False)
                post.session = session
                post.author = request.user
                post.save()
                # Notification logic here...
                return redirect('study_sessions:session_detail', session_id=session.id)
        
        elif 'resource_type' in request.POST: # Handle resource upload
            resource_form = SessionResourceForm(request.POST, request.FILES)
            if resource_form.is_valid():
                resource = resource_form.save(commit=False)
                resource.session = session
                resource.uploaded_by = request.user
                resource.save()
                return redirect('study_sessions:session_detail', session_id=session.id)

    post_form = SessionPostForm()
    resource_form = SessionResourceForm()
    
    context = {
        'session': session,
        'posts': session.posts.all(),
        'resources': session.resources.all(),
        'post_form': post_form,
        'resource_form': resource_form,
        'can_post': can_post,
    }

    if session.is_active:
        context.update({
            'total_seconds': session.duration_minutes * 60,
            'remaining_seconds': session.remaining_seconds,
        })
    else:
        # Data for the "ended" state
        contributors = session.posts.values('author__username').annotate(message_count=Count('id')).order_by('-message_count')
        context.update({
            'total_duration': session.duration_minutes,
            'total_notes': session.posts.count(),
            'contributors': contributors,
        })

    return render(request, 'studySessions/session_detail.html', context)

@login_required
def close_session(request, session_id):
    session = get_object_or_404(StudySession, id=session_id)
    if request.user == session.created_by:
        if request.method == 'POST':
            session.close()
            summary = generate_session_summary(session)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'status': 'ok',
                    'summary_id': summary.id,
                    'total_posts': summary.total_posts,
                    'participants_count': summary.participants_count,
                    'files_shared': summary.files_shared,
                    'auto_summary': summary.auto_summary,
                    'top_contributors': summary.top_contributors,
                    'session_title': session.title,
                    'duration_minutes': session.duration_minutes,
                })
            return redirect('study_sessions:session_detail', session_id=session.id)
    return redirect('study_sessions:session_detail', session_id=session.id)

@login_required
def session_history(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    sessions = StudySession.objects.filter(group=group, is_active=False).order_by('-start_time')
    paginator = Paginator(sessions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'studySessions/session_history.html', {'group': group, 'page_obj': page_obj})