from django.db import models
from django.contrib.auth.models import User

class Friendship(models.Model):
    from_user = models.ForeignKey(User, related_name='friendship_creator_set', on_delete=models.CASCADE)
    to_user = models.ForeignKey(User, related_name='friend_set', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} is friends with {self.to_user.username}"