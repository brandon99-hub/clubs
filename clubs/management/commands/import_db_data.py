import json
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clubs.models import Profile, Club, Event, Membership, Message
from django.db import transaction
from pathlib import Path

User = get_user_model()

class Command(BaseCommand):
    help = 'Import all data from a JSON file into the current database.'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='Path to the JSON file to import')

    @transaction.atomic
    def handle(self, *args, **options):
        json_file = options['json_file']
        if not Path(json_file).exists():
            self.stdout.write(self.style.ERROR(f'File not found: {json_file}'))
            return
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.stdout.write(self.style.SUCCESS(f'Loaded data from {json_file}'))

        # Import Users
        users = data['data'].get('users', {}).get('records', [])
        for u in users:
            obj, created = User.objects.get_or_create(
                id=u['id'],
                defaults={
                    'username': u['username'],
                    'email': u['email'],
                    'first_name': u['first_name'],
                    'last_name': u['last_name'],
                    'is_active': u['is_active'],
                    'is_staff': u['is_staff'],
                    'is_superuser': u['is_superuser'],
                    'date_joined': u['date_joined'],
                    'last_login': u['last_login'],
                }
            )
            if not created:
                # Optionally update fields
                pass
        self.stdout.write(self.style.SUCCESS(f'Imported {len(users)} users'))

        # Import Profiles
        profiles = data['data'].get('profiles', {}).get('records', [])
        for p in profiles:
            user = User.objects.filter(id=p['user_id']).first()
            if not user:
                continue
            obj, created = Profile.objects.get_or_create(
                id=p['id'],
                defaults={
                    'user': user,
                    'profile_pic': p['profile_pic'],
                    'bio': p['bio'],
                    'updated_at': p['updated_at'],
                    'subscribed_to_emails': p['subscribed_to_emails'],
                }
            )
            if not created:
                # Optionally update fields
                pass
        self.stdout.write(self.style.SUCCESS(f'Imported {len(profiles)} profiles'))

        # Import Clubs
        clubs = data['data'].get('clubs', {}).get('records', [])
        for c in clubs:
            admin = User.objects.filter(id=c['admin_id']).first()
            if not admin:
                continue
            obj, created = Club.objects.get_or_create(
                id=c['id'],
                defaults={
                    'name': c['name'],
                    'description': c['description'],
                    'admin': admin,
                    'created_at': c['created_at'],
                    'banner': c['banner'],
                    'is_active': c['is_active'],
                }
            )
            if not created:
                # Optionally update fields
                pass
        self.stdout.write(self.style.SUCCESS(f'Imported {len(clubs)} clubs'))

        # Import Events
        events = data['data'].get('events', {}).get('records', [])
        for e in events:
            club = Club.objects.filter(id=e['club_id']).first()
            if not club:
                continue
            obj, created = Event.objects.get_or_create(
                id=e['id'],
                defaults={
                    'club': club,
                    'title': e['title'],
                    'description': e['description'],
                    'event_date': e['event_date'],
                    'status': e['status'],
                    'created_at': e['created_at'],
                    'image': e['image'],
                }
            )
            if not created:
                # Optionally update fields
                pass
        self.stdout.write(self.style.SUCCESS(f'Imported {len(events)} events'))

        # Import Memberships
        memberships = data['data'].get('memberships', {}).get('records', [])
        for m in memberships:
            user = User.objects.filter(id=m['user_id']).first()
            club = Club.objects.filter(id=m['club_id']).first()
            if not user or not club:
                continue
            obj, created = Membership.objects.get_or_create(
                id=m['id'],
                defaults={
                    'user': user,
                    'club': club,
                    'role': m['role'],
                    'status': m['status'],
                    'applied_at': m['applied_at'],
                }
            )
            if not created:
                # Optionally update fields
                pass
        self.stdout.write(self.style.SUCCESS(f'Imported {len(memberships)} memberships'))

        # Import Messages
        messages = data['data'].get('messages', {}).get('records', [])
        for msg in messages:
            club = Club.objects.filter(id=msg['club_id']).first()
            sender = User.objects.filter(id=msg['sender_id']).first()
            receiver = User.objects.filter(id=msg['receiver_id']).first() if msg['receiver_id'] else None
            if not club or not sender:
                continue
            obj, created = Message.objects.get_or_create(
                id=msg['id'],
                defaults={
                    'club': club,
                    'sender': sender,
                    'receiver': receiver,
                    'content': msg['content'],
                    'timestamp': msg['timestamp'],
                    'is_deleted': msg['is_deleted'],
                }
            )
            if not created:
                # Optionally update fields
                pass
        self.stdout.write(self.style.SUCCESS(f'Imported {len(messages)} messages'))

        self.stdout.write(self.style.SUCCESS('Database import completed!')) 