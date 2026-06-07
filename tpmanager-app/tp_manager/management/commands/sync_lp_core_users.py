from django.core.management.base import BaseCommand
from tp_manager.sync import sync_formations_from_lp_core, sync_users_from_lp_core

class Command(BaseCommand):
    help = 'Synchronise les utilisateurs et formations LP Core vers TP Manager.'
    def handle(self, *args, **options):
        fr = sync_formations_from_lp_core()
        ur = sync_users_from_lp_core()
        self.stdout.write(self.style.SUCCESS(f'Formations {fr}; utilisateurs {ur}'))
