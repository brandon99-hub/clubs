# Google Calendar Integration Setup Guide

This guide will help you set up Google Calendar integration for your Django Clubs application.

## Prerequisites

1. **Google Cloud Console Account**: You need a Google account with access to Google Cloud Console
2. **Django Project**: Your Django project should be running and accessible
3. **Environment Variables**: You'll need to set up environment variables for Google API credentials

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Calendar API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

## Step 2: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application" as the application type
4. Add authorized redirect URIs:
   - `http://localhost:8000/calendar/callback/` (for development)
   - `https://yourdomain.com/calendar/callback/` (for production)
5. Note down your **Client ID** and **Client Secret**

## Step 3: Configure Environment Variables

Create a `.env` file in your Django project root or set environment variables:

```bash
# Google Calendar API Configuration
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:8000/calendar/callback/
```

## Step 4: Update Django Settings

The settings are already configured in `DjangoProject24/settings.py`:

```python
# Google Calendar API Configuration
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID', 'your-google-client-id')
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET', 'your-google-client-secret')
GOOGLE_REDIRECT_URI = os.environ.get('GOOGLE_REDIRECT_URI', 'http://localhost:8000/calendar/callback/')
```

## Step 5: Run Migrations

The database migrations have already been created and applied:

```bash
python manage.py makemigrations
python manage.py migrate
```

## Step 6: Test the Integration

1. **Start your Django server**:
   ```bash
   python manage.py runserver
   ```

2. **Access the settings page**:
   - Go to `http://localhost:8000/settings/`
   - Look for the "Google Calendar Integration" section

3. **Connect Google Calendar**:
   - Click "Connect Google Calendar"
   - You'll be redirected to Google's OAuth consent screen
   - Grant permissions to access your Google Calendar
   - You'll be redirected back to your settings page

4. **Test event syncing**:
   - Create an event in one of your clubs
   - Go to the event detail page
   - Click "Sync to Calendar" to sync the event to Google Calendar
   - Or use "Sync All Events" from the admin dashboard

## Features Available

### For Club Admins:
- **Connect Google Calendar**: OAuth2 authentication flow
- **Sync Individual Events**: Sync specific events to Google Calendar
- **Sync All Events**: Bulk sync all events from your clubs
- **Automatic Reminders**: Events include email and popup reminders
- **Event Updates**: Changes to events are reflected in Google Calendar

### For All Users:
- **Add to Calendar**: Basic calendar link for any event
- **View Synced Status**: See which events are synced to Google Calendar

## Security Considerations

1. **Token Storage**: OAuth2 tokens are encrypted and stored in the database
2. **Token Refresh**: Tokens are automatically refreshed before expiry
3. **Scope Limitation**: Only calendar events scope is requested
4. **User Control**: Users can disconnect their Google Calendar at any time

## Troubleshooting

### Common Issues:

1. **"Invalid redirect URI" error**:
   - Ensure the redirect URI in Google Cloud Console matches your Django settings
   - Check for trailing slashes and protocol (http vs https)

2. **"Access denied" error**:
   - Make sure the Google Calendar API is enabled in your Google Cloud project
   - Check that your OAuth consent screen is configured

3. **"No valid credentials" error**:
   - Try disconnecting and reconnecting your Google Calendar
   - Check that your environment variables are set correctly

4. **Events not syncing**:
   - Verify that you're the admin of the club containing the events
   - Check the Django logs for any API errors

### Debug Mode:

To enable debug logging for Google Calendar operations, add to your settings:

```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'clubs.services.google_calendar': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## API Limits

- Google Calendar API has a quota of 1,000,000 requests per day
- Each event sync operation uses approximately 1-2 API calls
- The system includes automatic retry logic for failed requests

## Future Enhancements

Potential improvements for the Google Calendar integration:

1. **Two-way sync**: Sync changes from Google Calendar back to Django
2. **Calendar selection**: Allow users to choose which calendar to sync to
3. **Recurring events**: Support for recurring event patterns
4. **Attendee management**: Sync event attendees and RSVPs
5. **Multiple calendar support**: Sync to multiple Google Calendars

## Support

If you encounter issues with the Google Calendar integration:

1. Check the Django logs for error messages
2. Verify your Google Cloud Console configuration
3. Test with a simple event creation and sync
4. Ensure your Django server is accessible from the internet (for OAuth callback)

---

**Note**: This integration requires an active internet connection and valid Google API credentials to function properly. 