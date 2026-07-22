from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True)
    location = models.CharField(max_length=100, blank=True)
    github_url = models.URLField(blank=True)
    friends = models.ManyToManyField(User, related_name='friends', blank=True)
    blocked_users = models.ManyToManyField(User, related_name='blocked_by', blank=True)

    def __str__(self):
        return self.user.username

    @property
    def avatar_url(self):
        # Only return a URL when a file is set AND actually present in storage.
        # The DB can reference filenames whose files no longer exist on disk
        # (e.g. /media/* is gitignored, so uploads don't survive restarts/redeploys).
        # Returning None in that case lets templates fall back to the placeholder
        # instead of rendering a broken <img> that 404s.
        try:
            if self.avatar and self.avatar.storage.exists(self.avatar.name):
                return self.avatar.url
            return None
        except Exception:
            return None

class FriendRequest(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
    )
    sender = models.ForeignKey(User, related_name='sent_friend_requests', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"From {self.sender} to {self.receiver} ({self.status})"

class Notification(models.Model):
    NOTIF_TYPES = [
        ('friend_request', 'Friend Request'),
        ('session_start', 'Session Start'),
        ('group_invite', 'Group Invite'),
        ('new_post', 'New Post'),
        ('system', 'System'),
    ]
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='sent_notifications')
    notif_type = models.CharField(max_length=20, choices=NOTIF_TYPES)
    message = models.TextField()
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.notif_type}"

def create_notification(recipient, notif_type, message, link='', sender=None):
    """
    Helper to create a notification from anywhere in the codebase.
    """
    Notification.objects.create(
        recipient=recipient,
        sender=sender,
        notif_type=notif_type,
        message=message,
        link=link,
    )