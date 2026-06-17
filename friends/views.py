from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView
from .models import Friendship

class FriendListView(LoginRequiredMixin, ListView):
    model = Friendship
    template_name = 'friends/friend_list.html'
    context_object_name = 'friends'

    def get_queryset(self):
        return Friendship.objects.filter(from_user=self.request.user)