from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from clubs.models import Profile, Club, Event, Membership, Message
from django.db import connection
import json
from datetime import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Extract all current database data in detailed format'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database extraction...'))
        
        # Get database info
        with connection.cursor() as cursor:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
        
        data = {
            'extraction_timestamp': datetime.now().isoformat(),
            'database_info': {
                'tables': [table[0] for table in tables],
                'total_tables': len(tables)
            },
            'data': {}
        }
        
        # Extract User data
        self.stdout.write('Extracting User data...')
        users_data = []
        for user in User.objects.all():
            user_data = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat() if user.date_joined else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
            users_data.append(user_data)
        
        data['data']['users'] = {
            'count': len(users_data),
            'records': users_data
        }
        
        # Extract Profile data
        self.stdout.write('Extracting Profile data...')
        profiles_data = []
        for profile in Profile.objects.all():
            profile_data = {
                'id': profile.id,
                'user_id': profile.user.id,
                'user_username': profile.user.username,
                'profile_pic': str(profile.profile_pic) if profile.profile_pic else None,
                'bio': profile.bio,
                'updated_at': profile.updated_at.isoformat() if profile.updated_at else None,
                'subscribed_to_emails': profile.subscribed_to_emails,
            }
            profiles_data.append(profile_data)
        
        data['data']['profiles'] = {
            'count': len(profiles_data),
            'records': profiles_data
        }
        
        # Extract Club data
        self.stdout.write('Extracting Club data...')
        clubs_data = []
        for club in Club.objects.all():
            club_data = {
                'id': club.id,
                'name': club.name,
                'description': club.description,
                'admin_id': club.admin.id,
                'admin_username': club.admin.username,
                'created_at': club.created_at.isoformat() if club.created_at else None,
                'banner': str(club.banner) if club.banner else None,
                'is_active': club.is_active,
            }
            clubs_data.append(club_data)
        
        data['data']['clubs'] = {
            'count': len(clubs_data),
            'records': clubs_data
        }
        
        # Extract Event data
        self.stdout.write('Extracting Event data...')
        events_data = []
        for event in Event.objects.all():
            event_data = {
                'id': event.id,
                'club_id': event.club.id,
                'club_name': event.club.name,
                'title': event.title,
                'description': event.description,
                'event_date': event.event_date.isoformat() if event.event_date else None,
                'status': event.status,
                'created_at': event.created_at.isoformat() if event.created_at else None,
                'image': str(event.image) if event.image else None,
            }
            events_data.append(event_data)
        
        data['data']['events'] = {
            'count': len(events_data),
            'records': events_data
        }
        
        # Extract Membership data
        self.stdout.write('Extracting Membership data...')
        memberships_data = []
        for membership in Membership.objects.all():
            membership_data = {
                'id': membership.id,
                'user_id': membership.user.id,
                'user_username': membership.user.username,
                'club_id': membership.club.id,
                'club_name': membership.club.name,
                'role': membership.role,
                'status': membership.status,
                'applied_at': membership.applied_at.isoformat() if membership.applied_at else None,
            }
            memberships_data.append(membership_data)
        
        data['data']['memberships'] = {
            'count': len(memberships_data),
            'records': memberships_data
        }
        
        # Extract Message data
        self.stdout.write('Extracting Message data...')
        messages_data = []
        for message in Message.objects.all():
            message_data = {
                'id': message.id,
                'club_id': message.club.id,
                'club_name': message.club.name,
                'sender_id': message.sender.id,
                'sender_username': message.sender.username,
                'receiver_id': message.receiver.id if message.receiver else None,
                'receiver_username': message.receiver.username if message.receiver else None,
                'content': message.content,
                'timestamp': message.timestamp.isoformat() if message.timestamp else None,
                'is_deleted': message.is_deleted,
            }
            messages_data.append(message_data)
        
        data['data']['messages'] = {
            'count': len(messages_data),
            'records': messages_data
        }
        
        # Calculate totals
        total_records = sum([
            data['data']['users']['count'],
            data['data']['profiles']['count'],
            data['data']['clubs']['count'],
            data['data']['events']['count'],
            data['data']['memberships']['count'],
            data['data']['messages']['count']
        ])
        
        data['summary'] = {
            'total_records': total_records,
            'users_count': data['data']['users']['count'],
            'profiles_count': data['data']['profiles']['count'],
            'clubs_count': data['data']['clubs']['count'],
            'events_count': data['data']['events']['count'],
            'memberships_count': data['data']['memberships']['count'],
            'messages_count': data['data']['messages']['count']
        }
        
        # Save to file
        filename = f'database_extraction_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.stdout.write(self.style.SUCCESS(f'Database extraction completed!'))
        self.stdout.write(self.style.SUCCESS(f'Data saved to: {filename}'))
        self.stdout.write(self.style.SUCCESS(f'Total records extracted: {total_records}'))
        
        # Print summary
        self.stdout.write('\n=== DATABASE SUMMARY ===')
        self.stdout.write(f"Users: {data['data']['users']['count']}")
        self.stdout.write(f"Profiles: {data['data']['profiles']['count']}")
        self.stdout.write(f"Clubs: {data['data']['clubs']['count']}")
        self.stdout.write(f"Events: {data['data']['events']['count']}")
        self.stdout.write(f"Memberships: {data['data']['memberships']['count']}")
        self.stdout.write(f"Messages: {data['data']['messages']['count']}")
        self.stdout.write(f"Total Records: {total_records}") 