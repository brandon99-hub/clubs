from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile,Message  # Make sure you adjust this for your actual Profile model
import logging
from .tasks import send_new_message_email  # New Celery task

# Set up logging
logger = logging.getLogger(__name__)


@receiver(post_save, sender=Message)
def email_on_new_message(sender, instance, created, **kwargs):
    """Send email notification when a new message is created."""
    if created:
        try:
            # Check if the message has a receiver (individual message)
            if instance.receiver:
                # Fetch receiver's profile to get their email subscription preferences
                profile = Profile.objects.get(user=instance.receiver)

                if profile.subscribed_to_emails:  # Send email only if subscribed
                    # Call Celery task for asynchronous email sending
                    send_new_message_email.delay(
                        sender_name=instance.sender.username,
                        recipient_email=instance.receiver.email,
                        content=instance.content
                    )
                    logger.info(f"Email notification sent to {instance.receiver.email}.")
                else:
                    logger.info(f"User {instance.receiver.username} is not subscribed to email notifications.")
            else:
                # Handle club-wide messages (where no specific receiver exists)
                logger.info(f"Club-wide message created in club {instance.club.name}. No email notifications sent.")

        except Profile.DoesNotExist:
            # Handle case where profile is missing
            logger.warning(f"Profile for user {instance.receiver} does not exist. Email not sent.")

        except Exception as e:
            # Catch any other unforeseen errors and log them
            logger.error(f"An error occurred while sending email for message ID {instance.id}: {e}")

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
