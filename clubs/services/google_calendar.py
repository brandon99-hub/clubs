import os
import json
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.utils import timezone
from ..models import GoogleCalendarToken, Event

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.events']

class GoogleCalendarService:
    def __init__(self, user):
        self.user = user
        self.service = None
        
    def get_credentials(self):
        """Get or refresh OAuth2 credentials for the user"""
        try:
            # Try to get existing token from database
            token_model = GoogleCalendarToken.objects.get(user=self.user)
            
            credentials = Credentials(
                token=token_model.access_token,
                refresh_token=token_model.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=SCOPES
            )
            
            # Refresh token if needed
            if token_model.needs_refresh():
                if credentials and credentials.expired and credentials.refresh_token:
                    credentials.refresh(Request())
                    
                    # Update token in database
                    token_model.access_token = credentials.token
                    token_model.token_expiry = timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp())
                    token_model.save()
            
            return credentials
            
        except GoogleCalendarToken.DoesNotExist:
            return None
    
    def create_auth_url(self):
        """Create authorization URL for OAuth2 flow"""
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI  # Explicitly set redirect_uri
        return flow.authorization_url()[0]
    
    def exchange_code_for_token(self, authorization_code):
        """Exchange authorization code for access token"""
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
                }
            },
            SCOPES
        )
        flow.redirect_uri = settings.GOOGLE_REDIRECT_URI  # Explicitly set redirect_uri
        flow.fetch_token(code=authorization_code)
        credentials = flow.credentials
        # Save token to database
        GoogleCalendarToken.objects.update_or_create(
            user=self.user,
            defaults={
                'access_token': credentials.token,
                'refresh_token': credentials.refresh_token,
                'token_expiry': timezone.now() + timedelta(seconds=credentials.expiry.timestamp() - datetime.now().timestamp())
            }
        )
        return credentials
    
    def get_calendar_service(self):
        """Get Google Calendar service instance"""
        if self.service is None:
            credentials = self.get_credentials()
            if credentials:
                self.service = build('calendar', 'v3', credentials=credentials)
        return self.service
    
    def create_event(self, event):
        """Create event in Google Calendar"""
        service = self.get_calendar_service()
        if not service:
            return None, "No valid credentials"
        
        try:
            # Prepare event data
            event_data = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.event_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (event.event_date + timedelta(hours=1)).isoformat(),
                    'timeZone': 'UTC',
                },
                'location': event.club.name,
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day
                        {'method': 'popup', 'minutes': 30},  # 30 minutes
                    ],
                },
            }
            
            # Create event in Google Calendar
            created_event = service.events().insert(
                calendarId='primary',
                body=event_data
            ).execute()
            
            # Update event with Google Calendar ID
            event.google_calendar_id = created_event['id']
            event.calendar_synced = True
            event.save()
            
            return created_event, None
            
        except HttpError as error:
            return None, f"An error occurred: {error}"
    
    def update_event(self, event):
        """Update event in Google Calendar"""
        service = self.get_calendar_service()
        if not service:
            return None, "No valid credentials"
        
        if not event.google_calendar_id:
            return self.create_event(event)
        
        try:
            # Prepare event data
            event_data = {
                'summary': event.title,
                'description': event.description,
                'start': {
                    'dateTime': event.event_date.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': (event.event_date + timedelta(hours=1)).isoformat(),
                    'timeZone': 'UTC',
                },
                'location': event.club.name,
            }
            
            # Update event in Google Calendar
            updated_event = service.events().update(
                calendarId='primary',
                eventId=event.google_calendar_id,
                body=event_data
            ).execute()
            
            return updated_event, None
            
        except HttpError as error:
            return None, f"An error occurred: {error}"
    
    def delete_event(self, event):
        """Delete event from Google Calendar"""
        service = self.get_calendar_service()
        if not service or not event.google_calendar_id:
            return None, "No valid credentials or calendar ID"
        
        try:
            service.events().delete(
                calendarId='primary',
                eventId=event.google_calendar_id
            ).execute()
            
            # Clear calendar sync status
            event.google_calendar_id = None
            event.calendar_synced = False
            event.save()
            
            return True, None
            
        except HttpError as error:
            return None, f"An error occurred: {error}"
    
    def sync_all_events(self):
        """Sync all user's events to Google Calendar"""
        events = Event.objects.filter(club__admin=self.user, calendar_synced=False)
        results = []
        
        for event in events:
            result, error = self.create_event(event)
            results.append({
                'event': event,
                'success': result is not None,
                'error': error
            })
        
        return results 