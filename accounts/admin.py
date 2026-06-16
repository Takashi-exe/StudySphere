from django.contrib import admin
from .models import Profile, FriendRequest

class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'location', 'github_url')
    filter_horizontal = ('friends', 'blocked_users')

class FriendRequestAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'status', 'created_at')
    list_filter = ('status',)

admin.site.register(Profile, ProfileAdmin)
admin.site.register(FriendRequest, FriendRequestAdmin)
