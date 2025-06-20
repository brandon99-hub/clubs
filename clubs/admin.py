from django.contrib import admin
from .models import Club, Event, Membership, Message, Profile


# Club admin customization
@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'admin', 'created_at')  # Columns to display
    list_filter = ('created_at',)  # Add filters
    search_fields = ('name', 'admin__username')  # Search bar
    ordering = ('-created_at',)  # Order by recent


# Profile admin customization
@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'bio', 'updated_at')
    search_fields = ('user__username', 'bio')  # Search by username or bio
    ordering = ('-updated_at',)


# Membership admin customization with bulk actions
@admin.action(description='Approve selected memberships')
def approve_memberships(modeladmin, request, queryset):
    """
    Custom admin action to bulk approve selected memberships.
    """
    updated_count = queryset.filter(status='pending').update(status='approved')
    modeladmin.message_user(request, f"{updated_count} membership(s) have been approved.", level='success')


@admin.action(description='Reject selected memberships')
def reject_memberships(modeladmin, request, queryset):
    """
    Custom admin action to bulk reject selected memberships.
    """
    updated_count = queryset.filter(status='pending').update(status='rejected')
    modeladmin.message_user(request, f"{updated_count} membership(s) have been rejected.", level='warning')


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ('user', 'club', 'role', 'status', 'applied_at')
    list_filter = ('role', 'status', 'club')  # Add filters
    search_fields = ('user__username', 'club__name')  # Search by username, club name
    actions = [approve_memberships, reject_memberships]  # Add bulk actions


# Event admin customization
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'club', 'event_date', 'created_at')
    list_filter = ('event_date', 'club')  # Filter by event date
    ordering = ('-event_date',)


# Message admin customization
@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'club', 'content', 'timestamp')
    search_fields = ('sender__username', 'content', 'club__name')  # Search messages
