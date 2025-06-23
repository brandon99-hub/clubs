from django.core.management.base import BaseCommand
from clubs.models import Club
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Fix orphaned clubs by assigning them to an admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--admin-username',
            type=str,
            help='Username of the admin to assign to orphaned clubs',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking for orphaned clubs...'))
        
        # Find orphaned clubs
        orphaned_clubs = Club.objects.filter(admin__isnull=True)
        
        if not orphaned_clubs.exists():
            self.stdout.write(self.style.SUCCESS('No orphaned clubs found!'))
            return
        
        self.stdout.write(f'Found {orphaned_clubs.count()} orphaned clubs')
        
        # Get or create admin user
        admin_username = options.get('admin_username')
        
        if admin_username:
            try:
                admin_user = User.objects.get(username=admin_username)
                self.stdout.write(f'Using existing admin: {admin_username}')
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'User {admin_username} not found!'))
                return
        else:
            # Create a new admin user
            admin_user = User.objects.create_superuser(
                username='club_admin',
                email='admin@clubs.com',
                password='admin123'
            )
            self.stdout.write(f'Created new admin: {admin_user.username} (password: admin123)')
        
        # Fix orphaned clubs
        fixed_count = 0
        for club in orphaned_clubs:
            club.admin = admin_user
            club.save()
            self.stdout.write(f'Fixed club: {club.name}')
            fixed_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Fixed {fixed_count} orphaned clubs!'))
        self.stdout.write(f'All clubs now have admin: {admin_user.username}') 