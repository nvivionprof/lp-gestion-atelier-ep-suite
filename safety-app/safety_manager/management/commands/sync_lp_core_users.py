from django.core.management.base import BaseCommand
from safety_manager.sync import sync_users_from_lp_core

class Command(BaseCommand):
    help = 'Synchronise les utilisateurs LP Core vers Safety Manager.'
    def handle(self, *args, **options):
        report = sync_users_from_lp_core()
        self.stdout.write(self.style.SUCCESS(f"Synchronisation Safety terminée : {report['created']} créés, {report['updated']} mis à jour, {len(report['errors'])} erreurs."))
        for err in report['errors'][:20]:
            self.stdout.write(self.style.WARNING(err))
