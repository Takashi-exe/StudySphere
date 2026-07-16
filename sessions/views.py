from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.utils import timezone
from django.db.models import Count, Sum
from django.core.paginator import Paginator
from groups.models import StudyGroup, GroupMembership
from .models import StudySession, SessionPost, SessionComment, SessionSummary

@login_required
def create_session(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    if not GroupMembership.objects.filter(user=request.user, group=group, role='admin').exists():
        return HttpResponseForbidden("You are not an admin of this group.")

    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        duration_minutes = request.POST.get('duration_minutes', 60)
        
        session = StudySession.objects.create(
            group=group,
            title=title,
            description=description,
            created_by=request.user,
            duration_minutes=duration_minutes,
            start_time=timezone.now(),
            is_active=True
        )
        return redirect('sessions:session_detail', session_id=session.id)
    
    return render(request, 'sessions/create_session.html', {'group': group})

@login_required
def session_detail(request, session_id):
    session = get_object_or_404(
        StudySession.objects.select_related('group', 'created_by'),
        id=session_id
    )
    
    if session.is_expired() and session.is_active:
        close_session_logic(session)

    posts = session.posts.prefetch_related('comments__author__profile', 'author__profile')
    is_member = session.group.members.filter(id=request.user.id).exists()
    can_post = is_member and session.is_active

    if request.method == 'POST':
        if not can_post:
            return JsonResponse({'status': 'error', 'message': 'You cannot post in this session.'}, status=403)
        
        content = request.POST.get('content')
        if not content:
            return JsonResponse({'status': 'error', 'message': 'Content cannot be empty.'}, status=400)

        post = SessionPost.objects.create(session=session, author=request.user, content=content)
        return JsonResponse({'status': 'ok', 'post_id': str(post.id)})

    context = {
        'session': session,
        'posts': posts,
        'is_member': is_member,
        'can_post': can_post,
    }
    return render(request, 'sessions/session_detail.html', context)

@login_required
def add_comment(request, post_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed.'}, status=405)

    post = get_object_or_404(SessionPost.objects.select_related('session'), id=post_id)
    if not post.session.is_active:
        return JsonResponse({'status': 'error', 'message': 'This session is no longer active.'}, status=403)

    content = request.POST.get('content')
    if not content:
        return JsonResponse({'status': 'error', 'message': 'Content cannot be empty.'}, status=400)

    comment = SessionComment.objects.create(post=post, author=request.user, content=content)
    return JsonResponse({
        'status': 'ok',
        'comment': {
            'id': str(comment.id),
            'author': comment.author.username,
            'content': comment.content,
            'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
    })

@login_required
def close_session(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed.'}, status=405)

    session = get_object_or_404(StudySession, id=session_id)
    if not GroupMembership.objects.filter(user=request.user, group=session.group, role='admin').exists():
        return HttpResponseForbidden("You are not an admin of this group.")

    close_session_logic(session)
    return JsonResponse({'status': 'closed'})

def close_session_logic(session):
    session.is_active = False
    session.save()

    total_posts = session.posts.count()
    total_comments = SessionComment.objects.filter(post__session=session).count()
    participants_count = session.posts.values('author').distinct().count()

    SessionSummary.objects.create(
        session=session,
        total_posts=total_posts,
        total_comments=total_comments,
        participants_count=participants_count,
        ai_summary=''
    )

@login_required
def session_history(request, group_id):
    group = get_object_or_404(StudyGroup, id=group_id)
    sessions_list = StudySession.objects.filter(group=group, is_active=False).order_by('-start_time')
    paginator = Paginator(sessions_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'sessions/session_history.html', {'group': group, 'page_obj': page_obj})