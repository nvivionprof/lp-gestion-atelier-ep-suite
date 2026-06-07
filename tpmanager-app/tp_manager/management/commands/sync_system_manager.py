from django.core.management.base import BaseCommand
from tp_manager.sync import sync_systems_from_system_manager


class Command(BaseCommand):
    help = 'Synchronise les systèmes depuis System Manager vers TP Manager.'

    def handle(self, *args, **options):
        report = sync_systems_from_system_manager()
        errors = report.get('errors') or []
        if errors:
            self.stdout.write(self.style.WARNING(f'Synchronisation System Manager partielle/non bloquante : {report}'))
        else:
            self.stdout.write(self.style.SUCCESS(f'Systèmes synchronisés : {report}'))
