from django.utils.html import escape
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)

User = settings.AUTH_USER_MODEL


# Profile model for extended user details
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    profile_pic = models.ImageField(
        upload_to='profile_pics/',
        blank=True,
        null=True,
        default='profile_pics/placeholder.jpeg',  # Use MEDIA_ROOT path here
        verbose_name="Profile Picture",
        help_text="Upload a profile picture for the user."
    )

    bio = models.TextField(
        blank=True,
        verbose_name="Biography",
        help_text="Write a short bio for the user."
    )
    updated_at = models.DateTimeField(auto_now=True)
    subscribed_to_emails = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


# Signal to create/update profiles when a user is saved
@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)
    else:
        Profile.objects.get_or_create(user=instance)


class Club(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,  # Ensures every club has a unique name
        verbose_name="Club Name",
        help_text="Enter the unique name of the club."
    )
    description = models.TextField(verbose_name="Description")
    admin = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='administered_clubs',
        verbose_name="Club Admin"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    banner = models.ImageField(
        upload_to='club_banners/',
        null=True,
        blank=True,
        verbose_name="Club Banner",
        help_text="Optional banner image for the club."
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Is Active",
        help_text="Mark as false to deactivate the club instead of deleting it."
    )

    def __str__(self):
        return self.name

    def is_club_active(self):
        return self.is_active

    def is_user_member(self, user):
        """Check if a user is a member of this club (including admin)"""
        if user == self.admin:
            return True
        return self.memberships.filter(user=user, status='approved').exists()

    def get_all_members(self):
        """Get all members of the club including the admin"""
        members = list(self.memberships.filter(status='approved').select_related('user'))
        # Add admin if not already in the list
        admin_membership = next((m for m in members if m.user == self.admin), None)
        if not admin_membership:
            # Create a virtual membership for admin
            from django.contrib.auth.models import User
            admin_membership = type('obj', (object,), {
                'user': self.admin,
                'status': 'approved',
                'role': 'admin'
            })()
            members.insert(0, admin_membership)
        return members


class Event(models.Model):
    EVENT_STATUSES = (
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
    )
    
    REMINDER_CHOICES = (
        ('none', 'No Reminder'),
        ('15min', '15 minutes before'),
        ('1hour', '1 hour before'),
        ('1day', '1 day before'),
        ('1week', '1 week before'),
    )
    
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='events',
        verbose_name="Club"
    )
    title = models.CharField(max_length=100, verbose_name="Event Title")
    description = models.TextField(verbose_name="Event Description")
    event_date = models.DateTimeField(verbose_name="Event Date")
    status = models.CharField(
        max_length=10,
        choices=EVENT_STATUSES,
        default='upcoming',
        verbose_name="Event Status",
        help_text="Status of the event."
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    image = models.ImageField(
        upload_to='event_images/',
        null=True,
        blank=True,
        verbose_name="Event Image",
        help_text="Optional image for the event."
    )
    
    # Reminder fields
    reminder_sent = models.BooleanField(
        default=False,
        verbose_name="Reminder Sent",
        help_text="Whether reminder has been sent for this event"
    )
    reminder_time = models.CharField(
        max_length=10,
        choices=REMINDER_CHOICES,
        default='1day',
        verbose_name="Reminder Time",
        help_text="When to send reminder before event"
    )
    
    # Calendar integration fields
    google_calendar_id = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name="Google Calendar Event ID",
        help_text="ID of the event in Google Calendar"
    )
    calendar_synced = models.BooleanField(
        default=False,
        verbose_name="Synced to Calendar",
        help_text="Whether this event is synced to external calendar"
    )

    class Meta:
        ordering = ['event_date']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return f"{self.title} - {self.club.name}"
    
    def get_reminder_datetime(self):
        """Calculate when reminder should be sent based on reminder_time"""
        from datetime import timedelta
        
        reminder_times = {
            '15min': timedelta(minutes=15),
            '1hour': timedelta(hours=1),
            '1day': timedelta(days=1),
            '1week': timedelta(weeks=1),
        }
        
        if self.reminder_time in reminder_times:
            return self.event_date - reminder_times[self.reminder_time]
        return None
    
    def should_send_reminder(self):
        """Check if reminder should be sent now"""
        from django.utils import timezone
        
        reminder_datetime = self.get_reminder_datetime()
        if not reminder_datetime:
            return False
            
        now = timezone.now()
        # Send reminder if we're within 5 minutes of the reminder time
        return (reminder_datetime - timedelta(minutes=5)) <= now <= (reminder_datetime + timedelta(minutes=5))


class Membership(models.Model):
    ROLES = (
        ('member', 'Regular Member'),
        ('admin', 'Club Administrator'),
        ('moderator', 'Moderator with privileges'),
    )
    role = models.CharField(
        max_length=10,
        choices=ROLES,
        default='member',
        verbose_name="Membership Role",
        help_text="Define the role of the user in the club."
    )

    STATUS_CHOICES = (
        ('pending', 'Pending Approval'),
        ('approved', 'Membership Approved'),
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name="Membership Status",
        help_text="Approval status of the membership."
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="User"
    )
    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name="Club"
    )
    applied_at = models.DateTimeField(auto_now_add=True, verbose_name="Application Timestamp")

    class Meta:
        unique_together = ('user', 'club')  # Prevent duplicate memberships
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    def __str__(self):
        return f"{self.user.username} - {self.club.name} ({self.status})"

def get_default_user():
    user = get_user_model().objects.first()
    if not user:
        raise ValidationError("There are no users in the database to set a default receiver.")
    return user.id


class Message(models.Model):
    club = models.ForeignKey(
        "Club",  # Assumes a `Club` model exists
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name="Club"
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Sender",
        db_index=True
    )
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="received_messages",
        db_index=True,
        null=True,  # Make it optional
        blank=True  # Allow blank values

    )
    content = models.TextField(verbose_name="Message Content")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Timestamp", db_index=True)
    is_deleted = models.BooleanField(default=False)  # Soft delete flag

    class Meta:
        ordering = ['timestamp']  # Messages always ordered by timestamp
        verbose_name = "Message"
        verbose_name_plural = "Messages"

    def save(self, *args, **kwargs):
        """Validate and sanitize message before saving."""
        # Validation: Check if sender is a member of the club OR the club admin
        if not self.club.is_user_member(self.sender):
            raise ValidationError(f"{self.sender.username} is not a member of the club.")

        # Escape the content to prevent XSS attacks
        self.content = escape(self.content)

        # Save the message
        super().save(*args, **kwargs)

    def delete(self):
        """Perform a soft delete by setting `is_deleted` to True."""
        self.is_deleted = True
        self.save()

    def __str__(self):
        return f"Message from {self.sender.username} in {self.club.name}"


class Notification(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    club = models.ForeignKey('Club', on_delete=models.CASCADE, related_name='notifications')
    message = models.ForeignKey('Message', on_delete=models.CASCADE, related_name='notifications', null=True, blank=True)
    content = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Notification'
        verbose_name_plural = 'Notifications'

    def __str__(self):
        return f"Notification for {self.user} in {self.club}: {self.content}"


class Document(models.Model):
    club = models.ForeignKey(
        "Club",
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Club"
    )
    title = models.CharField(max_length=200, verbose_name="Document Title")
    description = models.TextField(blank=True, verbose_name="Description")
    file = models.FileField(
        upload_to='club_documents/',
        verbose_name="Document File"
    )
    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Uploaded By"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Upload Date")
    is_public = models.BooleanField(
        default=True,
        verbose_name="Public Document",
        help_text="If checked, all club members can view this document"
    )

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = "Document"
        verbose_name_plural = "Documents"

    def __str__(self):
        return f"{self.title} - {self.club.name}"

    def get_file_extension(self):
        """Get the file extension for display purposes"""
        if self.file:
            return self.file.name.split('.')[-1].upper()
        return ''

    def get_file_size(self):
        """Get file size in human readable format"""
        if self.file:
            size = self.file.size
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
        return '0 B'


class GoogleCalendarToken(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='google_calendar_token',
        verbose_name="User"
    )
    access_token = models.TextField(verbose_name="Access Token")
    refresh_token = models.TextField(verbose_name="Refresh Token")
    token_expiry = models.DateTimeField(verbose_name="Token Expiry")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")

    class Meta:
        verbose_name = "Google Calendar Token"
        verbose_name_plural = "Google Calendar Tokens"

    def __str__(self):
        return f"Google Calendar Token for {self.user.username}"

    def is_expired(self):
        """Check if the token is expired"""
        from django.utils import timezone
        return timezone.now() >= self.token_expiry

    def needs_refresh(self):
        """Check if token needs refresh (5 minutes before expiry)"""
        from django.utils import timezone
        from datetime import timedelta
        return timezone.now() >= (self.token_expiry - timedelta(minutes=5))
