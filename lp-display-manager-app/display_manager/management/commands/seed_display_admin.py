import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or reset the local LP Display Manager admin account.'

    def handle(self, *args, **options):
        username = os.getenv('LPDISPLAY_ADMIN_USERNAME', 'admin')
        password = os.getenv('LPDISPLAY_ADMIN_PASSWORD', 'admin')
        reset = os.getenv('LPDISPLAY_ADMIN_RESET', '1') == '1'
        User = get_user_model()
        user, created = User.objects.get_or_create(username=username)
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        if created or reset or not user.has_usable_password():
            user.set_password(password)
        user.save()
        self.stdout.write(self.style.SUCCESS(f'LP Display admin OK: {username}'))
