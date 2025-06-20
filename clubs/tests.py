from django.test import TestCase
from django.urls import reverse
from .models import Club,Profile,Message
from django.core.exceptions import ValidationError
from unittest.mock import patch
from django.contrib.auth.models import User

class MessageModelTest(TestCase):
    def setUp(self):
        # Create users and profiles
        self.sender = User.objects.create(username="sender")
        self.receiver = User.objects.create(username="receiver")
        Profile.objects.create(user=self.receiver, subscribed_to_emails=True)

        # Create club
        self.club = Club.objects.create(name="Chess Club", description="Chess enthusiasts")

    def test_message_creation(self):
        # Valid message creation
        message = Message.objects.create(
            club=self.club,
            sender=self.sender,
            receiver=self.receiver,
            content="Hello, this is a test message!"
        )
        self.assertEqual(message.sender, self.sender)
        self.assertEqual(message.receiver, self.receiver)
        self.assertEqual(message.club, self.club)

    def test_message_validation(self):
        # Ensure ValidationError is raised if receiver is missing
        with self.assertRaises(ValidationError):
            message = Message(
                club=self.club,
                sender=self.sender,
                receiver=None,  # Missing receiver
                content="Hello!"
            )
            message.save()

    @patch("app.tasks.send_new_message_email.delay")
    def test_email_notification_signal(self, mock_send_email):
        # Trigger message creation and check if email task is triggered
        Message.objects.create(
            club=self.club,
            sender=self.sender,
            receiver=self.receiver,
            content="This is a test message"
        )
        self.assertTrue(mock_send_email.called)
        mock_send_email.assert_called_with(
            sender_name=self.sender.username,
            recipient_email=self.receiver.email,
            content="This is a test message"
        )


class ClubListViewTest(TestCase):
    def setUp(self):
        # Set up multiple test clubs
        Club.objects.create(name="Chess Club", description="A place to enjoy chess")
        Club.objects.create(name="Basketball Club", description="A basketball team")
        Club.objects.create(name="Drama Club", description="Let your acting skills shine")

    def test_club_list_view(self):
        response = self.client.get(reverse('club_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'clubs/club_list.html')

    def test_club_list_search(self):
        # Test search functionality
        response = self.client.get(reverse('club_list') + '?q=chess')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Chess Club")
        self.assertNotContains(response, "Basketball Club")

        response = self.client.get(reverse('club_list') + '?q=team')
        self.assertContains(response, "Basketball Club")
        self.assertNotContains(response, "Drama Club")

    def test_club_list_empty_search(self):
        response = self.client.get(reverse('club_list') + '?q=nonsense')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "No clubs found.")




