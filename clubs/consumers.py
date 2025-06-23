import json
from channels.generic.websocket import AsyncWebsocketConsumer
import urllib.parse
import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from asgiref.sync import sync_to_async  # Added for async email handling
from DjangoProject24 import settings
import re  # Added for validation

logger = logging.getLogger(__name__)


def send_html_email(subject, context, recipient_email, template_name):
    """Utility function to send HTML emails."""
    email_body = render_to_string(template_name, context)
    email = EmailMessage(
        subject, email_body, settings.DEFAULT_FROM_EMAIL, [recipient_email]
    )
    email.content_subtype = 'html'
    email.send()


async def send_email_async(subject, context, recipient_email, template_name):
    """Asynchronous wrapper for sending HTML emails."""
    await sync_to_async(send_html_email)(
        subject=subject,
        context=context,
        recipient_email=recipient_email,
        template_name=template_name,
    )


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        user = self.scope.get('user')

        if user and user.is_authenticated:
            room_name = self.scope.get('url_route', {}).get('kwargs', {}).get('room_name')

            # Room name validation
            if not room_name or not re.match(r'^[a-zA-Z0-9_-]+$', room_name):  # Ensure valid room name
                logger.error("Invalid room name provided during connection.")
                await self.close()
                return

            self.room_name = urllib.parse.unquote(room_name)
            self.room_group_name = f'chat_{self.room_name}'
            username = getattr(user, 'username', 'Anonymous')  # Extract username safely for logging

            logger.info(f"User '{username}' trying to connect to room '{self.room_name}'")

            # Join room group
            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
            except AttributeError:
                logger.error("Channel layer is improperly configured or unavailable.")
                await self.close()
        else:
            client_ip = self.scope.get('client', [None])[0]
            logger.warning(f"Unauthenticated connection attempt from IP: {client_ip}")
            await self.close()

    async def disconnect(self, close_code):
        try:
            # Leave room group if room_group_name exists
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
        except AttributeError as e:
            logger.error(f"Channel layer misconfiguration during disconnection: {str(e)}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {str(e)}")

    async def receive(self, text_data):
        try:
            try:
                data = json.loads(text_data)
            except json.JSONDecodeError as e:
                logger.error(f"Malformed JSON received: {text_data} | Error: {str(e)}")
                await self.send(text_data=json.dumps({"error": "Malformed JSON"}))  # Inform client
                return

            if "message" in data:
                message = data["message"]
                username = data.get("username", "Unknown")  # Safely fetch username
                recipient_email = data.get("recipient_email")  # Optional key passed from frontend

                # Validate message content
                if not isinstance(message, str) or not message.strip() or len(message) > 500:
                    logger.warning(f"Invalid message received: {message}")
                    await self.send(text_data=json.dumps({"error": "Invalid message format"}))
                    return

                # Broadcast message to the room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'send_message',
                        'message': message,
                        'username': username,
                    }
                )

                # If recipient email is provided, send an email notification
                if recipient_email and isinstance(recipient_email, str) and '@' in recipient_email:
                    try:
                        await send_email_async(
                            subject="You have a new message!",
                            context={"sender": username, "message": message},
                            recipient_email=recipient_email,
                            template_name="emails/new_message.html"
                        )
                        logger.info(f"Email notification sent to {recipient_email}")
                    except Exception as e:
                        logger.error(f"Error sending email notification: {str(e)}")
            elif "typing" in data and isinstance(data["typing"], bool):
                typing = data["typing"]
                username = data.get("username", "Unknown")  # Safely fetch username

                # Broadcast typing state to the room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'typing': typing,
                        'username': username,
                    }
                )
            else:
                logger.warning("Received unexpected data format.")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {str(e)}")

    async def user_typing(self, event):
        typing = event['typing']
        username = event['username']

        # Send typing state to WebSocket
        await self.send(text_data=json.dumps({
            'typing': typing,
            'username': username,
        }))

    async def send_message(self, event):
        message = event['message']
        username = event['username']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'username': username,
        }))
