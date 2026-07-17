from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.contrib.auth.models import User
from django.db.models import Q, Max, Count, Prefetch

def get_unique_conversations(user):
    """
    Helper function to get a deduplicated list of 1:1 conversations.
    """
    # Get conversations where the user is a participant and there are only 2 participants
    conversations = Conversation.objects.filter(participants=user).annotate(
        num_participants=Count('participants')
    ).filter(num_participants=2).prefetch_related(
        Prefetch('participants', queryset=User.objects.exclude(id=user.id))
    ).order_by('-messages__created_at')
    
    # The prefetch above ensures that conv.participants.all() will only contain the other user
    for conv in conversations:
        if conv.participants.all():
            conv.other_user = conv.participants.all()[0]

    return conversations

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
            # This part is for AJAX, which is no longer used, but we'll leave it for now
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': message.id,
                    'text': message.text,
                    'sender': message.sender.username,
                    'timestamp': message.created_at.strftime('%I:%M %p')
                })
            return redirect('messaging:conversation_detail', conversation_id=conversation_id)

    messages = conversation.messages.all().order_by('created_at')
    
    # Get all conversations for the inbox panel
    unique_conversations = get_unique_conversations(request.user)

    context = {
        'conversation': conversation,
        'messages': messages,
        'conversations': unique_conversations,
        'active_conversation_id': conversation.id
    }
    return render(request, 'messaging/conversation_detail.html', context)

@login_required
def start_conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    
    # Find existing 1-on-1 conversations
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user).annotate(num_participants=Count('participants')).filter(num_participants=2)

    if conversation.exists():
        return redirect('messaging:conversation_detail', conversation_id=conversation.first().id)
    else:
        # Create a new 1-on-1 conversation
        new_conversation = Conversation.objects.create()
        new_conversation.participants.add(request.user, other_user)
        return redirect('messaging:conversation_detail', conversation_id=new_conversation.id)