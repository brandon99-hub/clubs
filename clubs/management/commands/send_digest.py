from django.core.management.base import BaseCommand
from clubs.models import Profile, Message


class Command(BaseCommand):
    help = "Send periodic email digests for unread messages."

    def handle(self, *args, **kwargs):
        users = Profile.objects.filter(subscribed_to_emails=True)  # Example `subscribed_to_emails` field
        for user in users:
            unread_messages = Message.objects.filter(receiver=user.user, read=False)
            if unread_messages.exists():
                # Build the email content
                messages_content = "\n".join(
                    [f"- {msg.sender.username}: {msg.content}" for msg in unread_messages]
                )
                self.stdout.write(f"Sending digest to {user.user.email}...")
                # Send the email
                send_mail(
                    subject="Your Chatroom Message Digest",
                    message=f"You have {unread_messages.count()} unread messages:\n\n{messages_content}",
                    from_email="your_email@example.com",
                    recipient_list=[user.user.email],
                    fail_silently=False,
                )
            else:
                self.stdout.write(f"No unread messages for {user.user.email}.")
