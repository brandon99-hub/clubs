from django.template.loader import render_to_string
from django.core.mail import EmailMessage


def send_html_email(subject, context, recipient_email, template_name):
    """Utility function to send HTML emails."""
    email_body = render_to_string(template_name, context)
    email = EmailMessage(
        subject, email_body, None, [recipient_email]
    )
    email.content_subtype = 'html'
    email.send()
