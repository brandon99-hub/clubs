from django.core.management.base import BaseCommand
from clubs.models import Club, User
from django.contrib.auth import get_user_model

User = get_user_model()

class Command(BaseCommand):
    help = 'Check what clubs exist in the database'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Checking clubs in database...'))
        
        clubs = Club.objects.all()
        
        if not clubs.exists():
            self.stdout.write(self.style.WARNING('No clubs found in database!'))
            return
        
        self.stdout.write(f'Found {clubs.count()} clubs:')
        self.stdout.write('=' * 50)
        
        for club in clubs:
            self.stdout.write(f'Club ID: {club.id}')
            self.stdout.write(f'Name: {club.name}')
            self.stdout.write(f'Description: {club.description}')
            self.stdout.write(f'Created: {club.created_at}')
            self.stdout.write(f'Active: {club.is_active}')
            
            # Check admin
            if club.admin:
                self.stdout.write(f'Admin: {club.admin.username} (ID: {club.admin.id})')
            else:
                self.stdout.write(self.style.ERROR('Admin: NULL (orphaned club!)'))
            
            # Check memberships
            memberships = club.memberships.all()
            self.stdout.write(f'Memberships: {memberships.count()}')
            
            self.stdout.write('-' * 30)
        
        # Check for orphaned clubs (clubs with no admin)
        orphaned_clubs = Club.objects.filter(admin__isnull=True)
        if orphaned_clubs.exists():
            self.stdout.write(self.style.ERROR(f'\nORPHANED CLUBS (no admin): {orphaned_clubs.count()}'))
            for club in orphaned_clubs:
                self.stdout.write(f'  - {club.name} (ID: {club.id})') 