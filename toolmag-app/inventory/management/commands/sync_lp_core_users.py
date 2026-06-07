from django.core.management.base import BaseCommand
from inventory.core_sync import sync_users_from_lp_core

class Command(BaseCommand):
    help = 'Synchronise les utilisateurs locaux ToolMag depuis LP Core.'
    def add_arguments(self, parser):
        parser.add_argument('--force-password', action='store_true', help='Réécrit les mots de passe ToolMag avec le mot de passe initial exposé par LP Core')
    def handle(self, *args, **options):
        report = sync_users_from_lp_core(force_password=options['force_password'])
        self.stdout.write(self.style.SUCCESS(f"Synchronisation LP Core : {report['created']} créés, {report['updated']} mis à jour, {report['skipped']} ignorés."))
        for err in report['errors'][:30]:
            self.stdout.write(self.style.WARNING(err))
