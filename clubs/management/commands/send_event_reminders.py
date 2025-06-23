from django.core.management.base import BaseCommand
from django.utils import timezone
from clubs.models import Event, Notification
from clubs.utils.email_utils import send_html_email
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Send event reminders to club members'

    def handle(self, *args, **options):
        self.stdout.write('Starting event reminder process...')
        
        # Get all upcoming events that need reminders
        upcoming_events = Event.objects.filter(
            status='upcoming',
            reminder_sent=False,
            reminder_time__in=['15min', '1hour', '1day', '1week']
        )
        
        reminders_sent = 0
        
        for event in upcoming_events:
            if event.should_send_reminder():
                try:
                    # Get all club members
                    club_members = event.club.get_all_members()
                    
                    # Create in-app notifications
                    notifications_to_create = []
                    for member in club_members:
                        notifications_to_create.append(
                            Notification(
                                user=member.user,
                                club=event.club,
                                content=f"Reminder: '{event.title}' is happening {event.get_reminder_datetime().strftime('%B %d, %Y at %I:%M %p')} in {event.club.name}"
                            )
                        )
                    
                    if notifications_to_create:
                        Notification.objects.bulk_create(notifications_to_create)
                    
                    # Send email reminders (if user has email notifications enabled)
                    for member in club_members:
                        if hasattr(member.user, 'profile') and member.user.profile.subscribed_to_emails:
                            try:
                                context = {
                                    'user_name': member.user.username,
                                    'event_title': event.title,
                                    'event_date': event.event_date,
                                    'club_name': event.club.name,
                                    'reminder_time': event.reminder_time,
                                }
                                
                                send_html_email(
                                    subject=f"Event Reminder: {event.title}",
                                    context=context,
                                    recipient_email=member.user.email,
                                    template_name='emails/event_reminder.html'
                                )
                            except Exception as e:
                                logger.error(f"Failed to send email reminder to {member.user.email}: {e}")
                    
                    # Mark reminder as sent
                    event.reminder_sent = True
                    event.save()
                    
                    reminders_sent += 1
                    self.stdout.write(f"Sent reminder for event: {event.title}")
                    
                except Exception as e:
                    logger.error(f"Failed to send reminder for event {event.id}: {e}")
                    self.stdout.write(self.style.ERROR(f"Failed to send reminder for event {event.title}: {e}"))
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully sent {reminders_sent} event reminders')
        ) 