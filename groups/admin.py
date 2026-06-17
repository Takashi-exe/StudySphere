from django.contrib import admin
from .models import StudyGroup, GroupMembership

class GroupMembershipInline(admin.TabularInline):
    model = GroupMembership
    extra = 1

@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'is_private', 'created_at')
    list_filter = ('is_private', 'created_at')
    search_fields = ('name', 'description')
    inlines = [GroupMembershipInline]

@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'group', 'role', 'joined_at')
    list_filter = ('group', 'role', 'joined_at')
    search_fields = ('user__username', 'group__name')
