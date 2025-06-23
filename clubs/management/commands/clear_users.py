from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clubs.models import Profile, Membership, Message
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Delete all users and related data to start fresh'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Clearing all users and related data...'))
        
        # Delete all messages first (they reference users)
        message_count = Message.objects.count()
        Message.objects.all().delete()
        self.stdout.write(f'Deleted {message_count} messages')
        
        # Delete all memberships
        membership_count = Membership.objects.count()
        Membership.objects.all().delete()
        self.stdout.write(f'Deleted {membership_count} memberships')
        
        # Delete all profiles
        profile_count = Profile.objects.count()
        Profile.objects.all().delete()
        self.stdout.write(f'Deleted {profile_count} profiles')
        
        # Delete all users
        user_count = User.objects.count()
        User.objects.all().delete()
        self.stdout.write(f'Deleted {user_count} users')
        
        self.stdout.write(self.style.SUCCESS('All users and related data cleared!'))
        self.stdout.write('You can now create fresh users via Django admin or management commands.') 