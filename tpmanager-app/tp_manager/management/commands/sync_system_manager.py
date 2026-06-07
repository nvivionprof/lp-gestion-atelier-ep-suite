from django.core.management.base import BaseCommand
from tp_manager.sync import sync_systems_from_system_manager

class Command(BaseCommand):
    help = 'Synchronise les systèmes pédagogiques depuis System Manager.'
    def handle(self, *args, **options):
        report = sync_systems_from_system_manager()
        self.stdout.write(self.style.SUCCESS(str(report)))
