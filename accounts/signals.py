from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import Profile

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        # Ensure profile exists for existing users, create if not.
        # This handles cases like the admin user created before the signal was in place.
        profile, created = Profile.objects.get_or_create(user=instance)
        if not created:
            # If the profile already existed, save it to trigger any potential updates.
            profile.save()
