from django.core.management.base import BaseCommand
from core.importers import import_users_xlsx

class Command(BaseCommand):
    help = 'Importe des utilisateurs depuis un fichier Excel compatible ToolMag/LP Core.'
    def add_arguments(self, parser):
        parser.add_argument('path')
    def handle(self, *args, **options):
        report = import_users_xlsx(options['path'], source='command')
        self.stdout.write(self.style.SUCCESS(f"Import terminé : {report['created']} créés, {report['updated']} mis à jour."))
        for err in report['errors'][:30]:
            self.stdout.write(self.style.WARNING(err))
