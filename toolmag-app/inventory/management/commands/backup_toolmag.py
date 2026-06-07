import os
import time
from django.conf import settings
from django.core.management.base import BaseCommand
from inventory.backup_utils import create_backup


class Command(BaseCommand):
    help = 'Sauvegarde ToolMag : base SQLite + media, avec rétention configurable.'

    def add_arguments(self, parser):
        parser.add_argument('--loop', action='store_true', help='Exécuter la sauvegarde en boucle.')
        parser.add_argument('--interval', type=int, default=86400, help='Intervalle en secondes en mode boucle. Défaut : 86400.')
        parser.add_argument('--retain-days', type=int, default=int(os.getenv('BACKUP_RETENTION_DAYS', '7')), help='Rétention des sauvegardes automatiques en jours. Défaut : 7.')
        parser.add_argument('--backup-dir', default=os.getenv('BACKUP_DIR', str(settings.BASE_DIR / 'backups')), help='Dossier de sauvegarde.')
        parser.add_argument('--type', choices=['auto', 'manual', 'pre_restore'], default='auto', help='Type de sauvegarde. Les sauvegardes manuelles et pre_restore ne sont pas purgées automatiquement.')
        parser.add_argument('--note', default='', help='Commentaire libre inscrit dans les métadonnées de sauvegarde.')

    def handle(self, *args, **options):
        if options['loop']:
            self.stdout.write(self.style.SUCCESS('Service de sauvegarde automatique ToolMag démarré.'))
            while True:
                self._run_backup(options)
                time.sleep(options['interval'])
        else:
            self._run_backup(options)

    def _run_backup(self, options):
        archive = create_backup(
            backup_type=options['type'],
            backup_dir_path=options['backup_dir'],
            retain_days=options['retain_days'],
            note=options.get('note') or '',
        )
        self.stdout.write(self.style.SUCCESS(f'Sauvegarde créée : {archive}'))
