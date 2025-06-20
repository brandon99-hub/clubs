from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_new_message_email(sender_name, recipient_email, content):
    """Send an email notification asynchronously."""
    try:
        subject = "You have a new message!"
        message = f"{sender_name} sent you a message: {content}"
        send_mail(subject, message, "no-reply@example.com", [recipient_email])
    except Exception as e:
        # Log email sending issues (if using a logger)
        print(f"Email sending failed: {e}")
