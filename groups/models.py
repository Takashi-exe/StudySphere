import uuid
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

class StudyGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(upload_to='group_covers/', blank=True, null=True)
    created_by = models.ForeignKey(User, related_name='created_groups', on_delete=models.CASCADE)
    members = models.ManyToManyField(User, through='GroupMembership', related_name='study_groups')
    invite_code = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    is_private = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('groups:group_detail', kwargs={'pk': self.pk})

class GroupMembership(models.Model):
    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('member', 'Member'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'group')

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.get_role_display()})"

class Channel(models.Model):
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return f"#{self.name} in {self.group.name}"

class Message(models.Model):
    channel = models.ForeignKey(Channel, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content}"