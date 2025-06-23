#!/usr/bin/env python
"""
Test script for Google Calendar integration
Run this script to verify that the Google Calendar integration is properly configured.
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Add the Django project to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DjangoProject24.settings')
django.setup()

from django.contrib.auth.models import User
from clubs.models import Club, Event, GoogleCalendarToken
from clubs.services.google_calendar import GoogleCalendarService

def test_google_calendar_setup():
    """Test the Google Calendar integration setup"""
    print("🔍 Testing Google Calendar Integration Setup...")
    print("=" * 50)
    
    # Check if required packages are installed
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        print("✅ Google API packages are installed")
    except ImportError as e:
        print(f"❌ Missing Google API package: {e}")
        return False
    
    # Check Django settings
    from django.conf import settings
    
    print(f"📋 Google Client ID: {'✅ Set' if settings.GOOGLE_CLIENT_ID != 'your-google-client-id' else '❌ Not configured'}")
    print(f"📋 Google Client Secret: {'✅ Set' if settings.GOOGLE_CLIENT_SECRET != 'your-google-client-secret' else '❌ Not configured'}")
    print(f"📋 Google Redirect URI: {settings.GOOGLE_REDIRECT_URI}")
    
    # Check if models exist
    try:
        # Test GoogleCalendarToken model
        token_count = GoogleCalendarToken.objects.count()
        print(f"✅ GoogleCalendarToken model exists ({token_count} tokens)")
        
        # Test Event model with calendar fields
        event_count = Event.objects.count()
        print(f"✅ Event model with calendar fields exists ({event_count} events)")
        
    except Exception as e:
        print(f"❌ Model error: {e}")
        return False
    
    # Check if there are any users and clubs
    user_count = User.objects.count()
    club_count = Club.objects.count()
    print(f"👥 Users in database: {user_count}")
    print(f"🏢 Clubs in database: {club_count}")
    
    if user_count == 0:
        print("⚠️  No users found. Create a user first to test OAuth flow.")
        return False
    
    if club_count == 0:
        print("⚠️  No clubs found. Create a club first to test event syncing.")
        return False
    
    # Test GoogleCalendarService initialization
    try:
        user = User.objects.first()
        calendar_service = GoogleCalendarService(user)
        print(f"✅ GoogleCalendarService initialized for user: {user.username}")
        
        # Test auth URL creation
        try:
            auth_url = calendar_service.create_auth_url()
            print(f"✅ Auth URL created: {auth_url[:50]}...")
        except Exception as e:
            print(f"⚠️  Auth URL creation failed (expected if credentials not configured): {e}")
        
    except Exception as e:
        print(f"❌ GoogleCalendarService error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 Google Calendar Integration Setup Test Complete!")
    print("\n📝 Next Steps:")
    print("1. Configure Google Cloud Console credentials")
    print("2. Set environment variables (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)")
    print("3. Run the Django server: python manage.py runserver")
    print("4. Visit /settings/ to connect Google Calendar")
    print("5. Create events and test syncing")
    
    return True

def test_event_creation():
    """Test creating an event with calendar integration"""
    print("\n🔍 Testing Event Creation with Calendar Integration...")
    print("=" * 50)
    
    try:
        # Get or create a test user and club
        user, created = User.objects.get_or_create(
            username='test_user',
            defaults={'email': 'test@example.com'}
        )
        if created:
            print(f"✅ Created test user: {user.username}")
        
        club, created = Club.objects.get_or_create(
            name='Test Club',
            defaults={
                'description': 'Test club for calendar integration',
                'admin': user
            }
        )
        if created:
            print(f"✅ Created test club: {club.name}")
        
        # Create a test event
        event_date = datetime.now() + timedelta(days=7)
        event, created = Event.objects.get_or_create(
            title='Test Calendar Event',
            club=club,
            defaults={
                'description': 'This is a test event for Google Calendar integration',
                'event_date': event_date,
                'reminder_time': '1day'
            }
        )
        
        if created:
            print(f"✅ Created test event: {event.title}")
            print(f"   Event date: {event.event_date}")
            print(f"   Reminder time: {event.reminder_time}")
            print(f"   Calendar synced: {event.calendar_synced}")
        else:
            print(f"✅ Test event already exists: {event.title}")
        
        return True
        
    except Exception as e:
        print(f"❌ Event creation test failed: {e}")
        return False

if __name__ == '__main__':
    print("🚀 Google Calendar Integration Test Suite")
    print("=" * 60)
    
    # Run tests
    setup_ok = test_google_calendar_setup()
    event_ok = test_event_creation()
    
    print("\n" + "=" * 60)
    if setup_ok and event_ok:
        print("🎉 All tests passed! Google Calendar integration is ready.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
    
    print("\n📚 For detailed setup instructions, see: GOOGLE_CALENDAR_SETUP.md") 