from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.contrib.auth.models import User
from django.db.models import Q, Max, Count
from itertools import groupby
from django.http import JsonResponse

def get_unique_conversations(user):
    """
    Helper function to get a deduplicated list of 1:1 conversations.
    """
    conversations = user.conversations.annotate(
        last_message_time=Max('messages__created_at'),
        num_participants=Count('participants')
    ).filter(
        num_participants=2
    ).order_by('-last_message_time')

    seen_users = set()
    unique_conversations = []
    for conv in conversations.prefetch_related('participants'):
        other_users = [p for p in conv.participants.all() if p != user]
        if not other_users:
            continue
        other_user_id = other_users[0].id
        if other_user_id not in seen_users:
            seen_users.add(other_user_id)
            conv.other_user = other_users[0]
            unique_conversations.append(conv)
    return unique_conversations

@login_required
def conversation_list(request):
    unique_conversations = get_unique_conversations(request.user)
    return render(request, 'messaging/conversation_list.html', {'conversations': unique_conversations})

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('messaging:conversation_list')

    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            message = Message.objects.create(conversation=conversation, sender=request.user, text=text)
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': message.id,
                    'text': message.text,
                    'sender': message.sender.username,
                    'timestamp': message.created_at.strftime('%I:%M %p')
                })
            return redirect('messaging:conversation_detail', conversation_id=conversation_id)

    messages = conversation.messages.all().order_by('created_at')
    grouped_messages = {k: list(v) for k, v in groupby(messages, key=lambda m: m.created_at.date())}

    # Get all conversations for the inbox panel, with deduplication
    unique_conversations = get_unique_conversations(request.user)

    context = {
        'conversation': conversation,
        'grouped_messages': grouped_messages,
        'conversations': unique_conversations,
        'active_conversation_id': conversation.id
    }
    return render(request, 'messaging/conversation_detail.html', context)

@login_required
def start_conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Find existing 1-on-1 conversations
    conversation = Conversation.objects.filter(participants=request.user)\
        .filter(participants=other_user)\
        .annotate(num_participants=Count('participants'))\
        .filter(num_participants=2)

    if conversation.exists():
        return redirect('messaging:conversation_detail', conversation_id=conversation.first().id)
    else:
        # Create a new 1-on-1 conversation
        new_conversation = Conversation.objects.create()
        new_conversation.participants.add(request.user, other_user)
        return redirect('messaging:conversation_detail', conversation_id=new_conversation.id)