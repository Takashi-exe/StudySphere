from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Conversation, Message
from django.contrib.auth.models import User
from django.db.models import Q

@login_required
def conversation_list(request):
    conversations = request.user.conversations.all()
    return render(request, 'messaging/conversation_list.html', {'conversations': conversations})

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)
    if request.user not in conversation.participants.all():
        return redirect('conversation_list')
    
    if request.method == 'POST':
        text = request.POST.get('text')
        if text:
            Message.objects.create(conversation=conversation, sender=request.user, text=text)
            return redirect('conversation_detail', conversation_id=conversation_id)
            
    return render(request, 'messaging/conversation_detail.html', {'conversation': conversation})

@login_required
def start_conversation(request, username):
    other_user = get_object_or_404(User, username=username)
    conversation = Conversation.objects.filter(participants=request.user).filter(participants=other_user)
    if conversation.exists():
        return redirect('conversation_detail', conversation_id=conversation.first().id)
    else:
        new_conversation = Conversation.objects.create()
        new_conversation.participants.add(request.user, other_user)
        return redirect('conversation_detail', conversation_id=new_conversation.id)
