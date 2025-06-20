from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from clubs.models import Profile


class Command(BaseCommand):
    help = "Create profiles for users who do not already have one"

    def handle(self, *args, **kwargs):
        # Find users without profiles
        users_without_profiles = User.objects.filter(profile__isnull=True)
        for user in users_without_profiles:
            Profile.objects.create(user=user)
            self.stdout.write(f"Created profile for user: {user.username}")
        if not users_without_profiles:
            self.stdout.write("All users already have profiles!")
        else:
            self.stdout.write("Successfully created missing profiles.")
