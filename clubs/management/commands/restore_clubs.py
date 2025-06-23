import json
from django.core.management.base import BaseCommand
from clubs.models import Club
from django.contrib.auth import get_user_model
from django.db import transaction

User = get_user_model()

class Command(BaseCommand):
    help = 'Restore clubs from the JSON backup file'

    def add_arguments(self, parser):
        parser.add_argument(
            '--json-file',
            type=str,
            default='database_extraction_20250623_164705.json',
            help='Path to the JSON backup file'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        json_file = options['json_file']
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return
        
        # Get the existing admin user
        try:
            admin_user = User.objects.get(username='brandon')
            self.stdout.write(f'Using existing admin: {admin_user.username}')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('Admin user "brandon" not found! Please create it first.'))
            return
        
        # Get clubs from JSON
        clubs_data = data['data'].get('clubs', {}).get('records', [])
        
        if not clubs_data:
            self.stdout.write(self.style.WARNING('No clubs found in JSON file'))
            return
        
        self.stdout.write(f'Found {len(clubs_data)} clubs in backup')
        
        # Restore clubs
        restored_count = 0
        for club_data in clubs_data:
            # Check if club already exists
            existing_club = Club.objects.filter(name=club_data['name']).first()
            if existing_club:
                self.stdout.write(f'Club already exists: {club_data["name"]}')
                continue
            
            # Create new club
            club = Club.objects.create(
                name=club_data['name'],
                description=club_data['description'],
                admin=admin_user,  # Assign to brandon
                created_at=club_data['created_at'],
                banner=club_data['banner'] if club_data['banner'] else None,
                is_active=club_data['is_active']
            )
            
            self.stdout.write(f'Restored club: {club.name}')
            restored_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Restored {restored_count} clubs!'))
        self.stdout.write(f'All clubs now have admin: {admin_user.username}')
        
        # Show summary
        total_clubs = Club.objects.count()
        self.stdout.write(f'Total clubs in database: {total_clubs}') 