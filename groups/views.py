from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, DetailView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from .models import StudyGroup, GroupMembership, Channel, Message
from django.contrib.auth.models import User

class GroupCreateView(LoginRequiredMixin, CreateView):
    model = StudyGroup
    fields = ['name', 'description', 'cover_image', 'is_private']
    template_name = 'groups/group_form.html'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        group = form.save()
        GroupMembership.objects.create(user=self.request.user, group=group, role='admin')
        Channel.objects.create(group=group, name='general')
        return super().form_valid(form)

class GroupDetailView(LoginRequiredMixin, DetailView):
    model = StudyGroup
    template_name = 'groups/group_detail.html'
    context_object_name = 'group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        context['members'] = group.members.all()
        context['is_admin'] = GroupMembership.objects.filter(user=self.request.user, group=group, role='admin').exists()
        
        channels = group.channel_set.all()
        context['channels'] = channels
        
        channel_id = self.kwargs.get('channel_id')
        if channel_id:
            current_channel = get_object_or_404(Channel, id=channel_id, group=group)
        else:
            current_channel = channels.first()
        
        context['current_channel'] = current_channel
        if current_channel:
            context['messages'] = current_channel.message_set.all().order_by('created_at')
        else:
            context['messages'] = []
            
        return context

    def post(self, request, *args, **kwargs):
        group = self.get_object()
        channel_id = self.kwargs.get('channel_id')
        if not channel_id:
            channel = group.channel_set.first()
            if not channel:
                return redirect(group.get_absolute_url())
        else:
            channel = get_object_or_404(Channel, id=channel_id, group=group)

        content = request.POST.get('content')
        if content:
            Message.objects.create(channel=channel, user=request.user, content=content)

        return redirect('groups:channel_detail', pk=group.pk, channel_id=channel.id)

class GroupUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudyGroup
    fields = ['name', 'description', 'cover_image', 'is_private']
    template_name = 'groups/group_form.html'

    def test_func(self):
        group = self.get_object()
        return GroupMembership.objects.filter(user=self.request.user, group=group, role='admin').exists()

class GroupDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = StudyGroup
    template_name = 'groups/group_confirm_delete.html'
    success_url = reverse_lazy('groups:group_list')

    def test_func(self):
        group = self.get_object()
        return GroupMembership.objects.filter(user=self.request.user, group=group, role='admin').exists()

class GroupListView(LoginRequiredMixin, ListView):
    model = StudyGroup
    template_name = 'groups/group_list.html'
    context_object_name = 'groups'

    def get_queryset(self):
        return self.request.user.study_groups.all()