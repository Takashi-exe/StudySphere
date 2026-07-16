import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from groups.models import StudyGroup

class StudySession(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='sessions')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_sessions')
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=60)
    is_active = models.BooleanField(default=True)
    participants = models.ManyToManyField(User, related_name='participated_sessions', blank=True)

    @property
    def remaining_seconds(self):
        elapsed_seconds = (timezone.now() - self.start_time).total_seconds()
        return max(0, self.duration_minutes * 60 - elapsed_seconds)

    def close(self):
        self.is_active = False
        self.end_time = timezone.now()
        self.save()

    def __str__(self):
        return self.title

class SessionPost(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(StudySession, on_delete=models.CASCADE, related_name='posts')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Post by {self.author.username} in {self.session.title}"

class PostComment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    post = models.ForeignKey(SessionPost, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment by {self.author.username} on {self.post.id}"

class SessionSummary(models.Model):
    session = models.OneToOneField(
        StudySession,
        on_delete=models.CASCADE,
        related_name='summary'
    )
    total_posts = models.IntegerField(default=0)
    participants_count = models.IntegerField(default=0)
    files_shared = models.IntegerField(default=0)
    top_contributors = models.JSONField(default=list)
    auto_summary = models.TextField(blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Summary for {self.session.title}"