from django import template
from django.urls import reverse

register = template.Library()

@register.filter
def notification_url(notification):
    """
    Returns the appropriate URL for a notification based on its content.
    """
    content = notification.content.lower()
    
    # Membership request notifications - go to admin dashboard
    if "has requested to join" in content:
        return reverse('admin_dashboard')
    
    # Membership approval/rejection notifications - go to club detail
    elif "membership request" in content and ("approved" in content or "rejected" in content):
        return reverse('club_detail', kwargs={'club_id': notification.club.id})
    
    # Document sharing notifications - go to messaging (documents section)
    elif "new document" in content and "has been shared" in content:
        return reverse('messaging', kwargs={'club_id': notification.club.id}) + '#documents'
    
    # Event notifications - go to event list
    elif "new event" in content and "scheduled for" in content:
        return reverse('event_list', kwargs={'club_id': notification.club.id})
    
    # Event reminder notifications - go to event list
    elif "reminder:" in content and "is happening" in content:
        return reverse('event_list', kwargs={'club_id': notification.club.id})
    
    # Message notifications - go to messaging
    elif "new message from" in content:
        return reverse('messaging', kwargs={'club_id': notification.club.id})
    
    # Default fallback - go to club detail
    else:
        return reverse('club_detail', kwargs={'club_id': notification.club.id}) 