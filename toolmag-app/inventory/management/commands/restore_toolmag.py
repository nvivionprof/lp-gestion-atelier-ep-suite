import os
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from inventory.backup_utils import restore_backup_from_archive


class Command(BaseCommand):
    help = 'Restaure ToolMag depuis une archive .tar.gz. Crée une sauvegarde pre_restore avant restauration.'

    def add_arguments(self, parser):
        parser.add_argument('backup_name', help='Nom du fichier .tar.gz dans le dossier backups, ou chemin absolu.')
        parser.add_argument('--backup-dir', default=os.getenv('BACKUP_DIR', str(settings.BASE_DIR / 'backups')), help='Dossier de sauvegarde.')
        parser.add_argument('--no-pre-restore', action='store_true', help='Désactive la sauvegarde pré-restore. Déconseillé.')

    def handle(self, *args, **options):
        try:
            pre, restored = restore_backup_from_archive(
                options['backup_name'],
                backup_dir_path=options['backup_dir'],
                create_pre_restore=not options['no_pre_restore'],
                actor_label='commande',
            )
        except Exception as exc:
            raise CommandError(str(exc))
        if pre:
            self.stdout.write(self.style.SUCCESS(f'Sauvegarde pré-restore créée : {pre.name}'))
        self.stdout.write(self.style.SUCCESS(f'Restauration effectuée : {restored}'))
