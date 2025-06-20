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
        default='profile_pics/avatar_placeholder.png',  # Use MEDIA_ROOT path here
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


class Event(models.Model):
    EVENT_STATUSES = (
        ('upcoming', 'Upcoming'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
        ('canceled', 'Canceled'),
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

    class Meta:
        ordering = ['event_date']
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self):
        return f"{self.title} - {self.club.name}"


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
        # Validation: Check if sender is a member of the club
        if not Membership.objects.filter(club=self.club, user=self.sender, status='approved').exists():
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
