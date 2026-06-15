from django.core.management.base import BaseCommand
from pfmp_manager.schema_repair import repair_pfmp_rc16_schema


class Command(BaseCommand):
    help = "Répare automatiquement le schéma PFMP RC16/RC17 si une migration a été partiellement appliquée."

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-mark-migration',
            action='store_true',
            help="Répare les objets mais ne marque pas pfmp_manager.0002 comme appliquée.",
        )

    def handle(self, *args, **options):
        repair_pfmp_rc16_schema(mark_migration=not options['no_mark_migration'], stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS('Réparation PFMP RC16/RC17 terminée.'))
