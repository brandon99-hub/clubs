# Generated by Django 5.2.3 on 2025-06-23 18:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('clubs', '0011_event_calendar_synced_event_google_calendar_id_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='GoogleCalendarToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('access_token', models.TextField(verbose_name='Access Token')),
                ('refresh_token', models.TextField(verbose_name='Refresh Token')),
                ('token_expiry', models.DateTimeField(verbose_name='Token Expiry')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Created At')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Updated At')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='google_calendar_token', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'verbose_name': 'Google Calendar Token',
                'verbose_name_plural': 'Google Calendar Tokens',
            },
        ),
    ]
