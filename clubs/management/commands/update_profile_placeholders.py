from django.core.management.base import BaseCommand
from clubs.models import Profile

class Command(BaseCommand):
    help = 'Set placeholder.jpeg as the profile picture for all users with no profile_pic or with the old placeholder.'

    def handle(self, *args, **options):
        updated = 0
        # Update profiles with null profile_pic
        for profile in Profile.objects.filter(profile_pic__isnull=True):
            profile.profile_pic = 'profile_pics/placeholder.jpeg'
            profile.save()
            updated += 1
        # Update profiles with blank profile_pic
        for profile in Profile.objects.filter(profile_pic=''):
            profile.profile_pic = 'profile_pics/placeholder.jpeg'
            profile.save()
            updated += 1
        # Update profiles with the old placeholder
        for profile in Profile.objects.filter(profile_pic='profile_pics/avatar_placeholder.png'):
            profile.profile_pic = 'profile_pics/placeholder.jpeg'
            profile.save()
            updated += 1
        self.stdout.write(self.style.SUCCESS(f'Updated {updated} profiles with placeholder.jpeg')) 