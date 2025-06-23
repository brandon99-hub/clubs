from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile,Message,Membership,Club,Notification,Document,Event  # Make sure you adjust this for your actual Profile model
import logging
from .tasks import send_new_message_email  # New Celery task
from .utils.email_utils import send_html_email  # Import the email utility

# Set up logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """Create or update user profile when a user is saved."""
    if created:
        # Only create profile if it doesn't exist
        Profile.objects.get_or_create(user=instance)
    else:
        # Update existing profile
        try:
            instance.profile.save()
        except Profile.DoesNotExist:
            # Create profile if it doesn't exist (for existing users)
            Profile.objects.create(user=instance)

@receiver(post_save, sender=Membership)
def email_on_new_membership(sender, instance, created, **kwargs):
    """Send email notification to club admin when a new membership request is created."""
    if created and instance.status == 'pending':
        club = instance.club
        admin = club.admin
        subject = f"New membership request for {club.name}"
        context = {
            'admin_username': admin.username,
            'requester_username': instance.user.username,
            'club_name': club.name,
        }
        send_html_email(
            subject,
            context,
            admin.email,
            'emails/new_membership_request.html'
        )

@receiver(post_save, sender=Membership)
def create_membership_notification(sender, instance, created, **kwargs):
    """Create notifications for membership requests, approvals, and rejections."""
    if created and instance.status == 'pending':
        # Create notification for the club admin when someone requests to join
        Notification.objects.create(
            user=instance.club.admin,
            club=instance.club,
            content=f"{instance.user.username} has requested to join {instance.club.name}"
        )
    elif not created and instance.status in ['approved', 'declined']:
        # Create notification for the user when their request is approved/rejected
        status_text = "approved" if instance.status == 'approved' else "rejected"
        Notification.objects.create(
            user=instance.user,
            club=instance.club,
            content=f"Your membership request for {instance.club.name} has been {status_text}"
        )

@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """Create notifications for club members when a new message is created."""
    if created:
        # Get all approved members of the club (excluding the sender)
        club_members = Membership.objects.filter(
            club=instance.club, 
            status='approved'
        ).exclude(user=instance.sender).values_list('user', flat=True)
        
        # Always include the club admin if they're not the sender
        if instance.club.admin != instance.sender:
            club_members = list(club_members) + [instance.club.admin.id]
        
        # Create notifications for all club members
        notifications_to_create = []
        for member_id in club_members:
            notifications_to_create.append(
                Notification(
                    user_id=member_id,
                    club=instance.club,
                    message=instance,
                    content=f"New message from {instance.sender.username} in {instance.club.name}"
                )
            )
        
        # Bulk create notifications for better performance
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

@receiver(post_save, sender=Document)
def create_document_notification(sender, instance, created, **kwargs):
    """Create notifications for club members when a new document is uploaded."""
    if created:
        # Get all approved members of the club (excluding the uploader)
        club_members = Membership.objects.filter(
            club=instance.club, 
            status='approved'
        ).exclude(user=instance.uploaded_by).values_list('user', flat=True)
        
        # Always include the club admin if they're not the uploader
        if instance.club.admin != instance.uploaded_by:
            club_members = list(club_members) + [instance.club.admin.id]
        
        # Create notifications for all club members
        notifications_to_create = []
        for member_id in club_members:
            notifications_to_create.append(
                Notification(
                    user_id=member_id,
                    club=instance.club,
                    content=f"New document '{instance.title}' has been shared in {instance.club.name}. Check the documents section!"
                )
            )
        
        # Bulk create notifications for better performance
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)

@receiver(post_save, sender=Event)
def create_event_reminder_notification(sender, instance, created, **kwargs):
    """Create notifications for event reminders."""
    if created and instance.reminder_time != 'none':
        # Get all members of the club
        club_members = instance.club.get_all_members()
        
        # Create notifications for all club members
        notifications_to_create = []
        for member in club_members:
            notifications_to_create.append(
                Notification(
                    user=member.user,
                    club=instance.club,
                    content=f"New event '{instance.title}' scheduled for {instance.event_date.strftime('%B %d, %Y at %I:%M %p')} in {instance.club.name}"
                )
            )
        
        # Bulk create notifications for better performance
        if notifications_to_create:
            Notification.objects.bulk_create(notifications_to_create)
