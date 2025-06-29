import json
from channels.generic.websocket import AsyncWebsocketConsumer
import urllib.parse
import logging
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from asgiref.sync import sync_to_async, database_sync_to_async
from DjangoProject24 import settings
import re
from clubs.models import Message, Club
from django.contrib.auth import get_user_model

logger = logging.getLogger(__name__)
User = get_user_model()


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
        self.user = self.scope.get('user')

        if self.user and self.user.is_authenticated:
            raw_room_name = self.scope.get('url_route', {}).get('kwargs', {}).get('room_name')

            if not raw_room_name or not re.match(r'^[a-zA-Z0-9_-]+$', raw_room_name):
                logger.error(f"Invalid room name provided during connection: {raw_room_name}")
                await self.close()
                return

            self.room_name = urllib.parse.unquote(raw_room_name) # e.g., "club_123"
            self.room_group_name = f'chat_{self.room_name}'

            # Extract club_id from room_name (e.g., "club_123" -> 123)
            try:
                club_id_str = self.room_name.split('_')[-1]
                self.club_id = int(club_id_str)
            except (IndexError, ValueError):
                logger.error(f"Could not extract valid club_id from room_name: {self.room_name}")
                await self.close()
                return

            logger.info(f"User '{self.user.username}' trying to connect to room '{self.room_name}' (Club ID: {self.club_id})")

            # Check if user is a member of the club
            is_member = await self._check_user_membership()
            if not is_member:
                logger.warning(f"User '{self.user.username}' denied connection to '{self.room_name}': not a member.")
                await self.close()
                return

            try:
                await self.channel_layer.group_add(
                    self.room_group_name,
                    self.channel_name
                )
                await self.accept()
                logger.info(f"User '{self.user.username}' connected to room '{self.room_name}'")
            except AttributeError:
                logger.error("Channel layer is improperly configured or unavailable.")
                await self.close()
        else:
            client_ip = self.scope.get('client', [None])[0]
            logger.warning(f"Unauthenticated connection attempt from IP: {client_ip}")
            await self.close()

    @database_sync_to_async
    def _get_club(self, club_id):
        try:
            return Club.objects.get(id=club_id)
        except Club.DoesNotExist:
            return None

    @database_sync_to_async
    def _check_user_membership(self):
        if not hasattr(self, 'club_id'): # Should have been set in connect
             return False
        try:
            club = Club.objects.get(id=self.club_id)
            return club.is_user_member(self.user)
        except Club.DoesNotExist:
            logger.error(f"Club with ID {self.club_id} not found for membership check.")
            return False


    async def disconnect(self, close_code):
        try:
            if hasattr(self, 'room_group_name'):
                await self.channel_layer.group_discard(
                    self.room_group_name,
                    self.channel_name
                )
                logger.info(f"User '{getattr(self.user, 'username', 'Unknown')}' disconnected from room '{self.room_name}'")
        except AttributeError as e:
            logger.error(f"Channel layer misconfiguration during disconnection: {str(e)}")
        except Exception as e:
            logger.error(f"Error during WebSocket disconnection: {str(e)}")

    @database_sync_to_async
    def _save_message(self, club_id, sender_user, content, temp_id):
        try:
            club = Club.objects.get(id=club_id)
            # Validate sender membership again, just in case
            if not club.is_user_member(sender_user):
                logger.warning(f"Message save denied: User {sender_user} not a member of club {club_id}.")
                return None, "User is not a member of this club."

            message_obj = Message.objects.create(
                club=club,
                sender=sender_user,
                content=content
            )
            return message_obj, None
        except Club.DoesNotExist:
            logger.error(f"Club with ID {club_id} not found when trying to save message.")
            return None, "Club not found."
        except Exception as e:
            logger.error(f"Error saving message to database: {str(e)}")
            return None, f"Database error: {str(e)}"

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError as e:
            logger.error(f"Malformed JSON received: {text_data} | Error: {str(e)}")
            await self.send(text_data=json.dumps({"error": "Malformed JSON", "type": "error"}))
            return

        message_type = data.get('type')
        client_temp_id = data.get('temp_id') # Client sends a temporary ID for optimistic updates

        if message_type == 'chat_message':
            message_content = data.get("message")

            if not isinstance(message_content, str) or not message_content.strip() or len(message_content) > 500:
                logger.warning(f"Invalid message content received: {message_content}")
                await self.send(text_data=json.dumps({
                    "error": "Invalid message format",
                    "type": "error",
                    "temp_id": client_temp_id # Echo back temp_id for client-side error handling
                }))
                return

            if not self.user or not self.user.is_authenticated:
                logger.warning("Unauthenticated user tried to send a message.")
                await self.send(text_data=json.dumps({
                    "error": "Authentication required.",
                    "type": "error",
                    "temp_id": client_temp_id
                }))
                return

            # Save the message to the database
            saved_message, error_msg = await self._save_message(self.club_id, self.user, message_content, client_temp_id)

            if error_msg or not saved_message:
                logger.error(f"Failed to save message from {self.user.username}: {error_msg}")
                await self.send(text_data=json.dumps({
                    "error": f"Could not save message: {error_msg}",
                    "type": "error",
                    "temp_id": client_temp_id
                }))
                return

            # Prepare message data for broadcast, including database ID and timestamp
            message_data_for_broadcast = {
                'type': 'send_message', # This is the type for the group_send handler
                'message_id': saved_message.id,
                'content': saved_message.content,
                'username': saved_message.sender.username,
                'timestamp': saved_message.timestamp.isoformat(),
                'temp_id': client_temp_id, # Include temp_id for client reconciliation
                'sender_channel_name': self.channel_name # For potential future use, not strictly needed if client handles duplicates
            }

            # Broadcast message to the room group
            await self.channel_layer.group_send(
                self.room_group_name,
                message_data_for_broadcast
            )

            # Optional: Email notification (if needed, but not central to this change)
            # recipient_email = data.get("recipient_email")
            # if recipient_email: ...

        elif message_type == 'typing':
            typing_status = data.get("typing", False)
            if not self.user or not self.user.is_authenticated:
                logger.warning("Unauthenticated user tried to send typing indicator.")
                return

            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'user_typing', # This is the type for the group_send handler
                    'typing': typing_status,
                    'username': self.user.username,
                    'sender_channel_name': self.channel_name # Exclude sender from seeing their own typing
                }
            )
        else:
            logger.warning(f"Received unexpected WebSocket data type: {message_type}")
            await self.send(text_data=json.dumps({
                "error": "Unknown message type",
                "type": "error",
                "temp_id": client_temp_id
            }))


    async def user_typing(self, event):
        # This method handles the 'user_typing' event from group_send
        # Don't send typing indicator back to the user who is typing
        if self.channel_name != event.get('sender_channel_name'):
            await self.send(text_data=json.dumps({
                'type': 'typing', # type for client-side handling
                'typing': event['typing'],
                'username': event['username'],
            }))

    async def send_message(self, event):
        # This method handles the 'send_message' event from group_send
        # It sends the confirmed message (saved in DB) to the WebSocket client
        await self.send(text_data=json.dumps({
            'type': 'chat_message', # type for client-side handling
            'id': event['message_id'],
            'message': event['content'], # 'message' is the key client expects for content
            'username': event['username'],
            'timestamp': event['timestamp'],
            'temp_id': event.get('temp_id') # Pass back temp_id for client reconciliation
        }))
