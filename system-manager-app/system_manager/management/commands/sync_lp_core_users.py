from django.core.management.base import BaseCommand
from system_manager.sync import sync_users_from_lp_core, sync_formations_from_lp_core


class Command(BaseCommand):
    help = 'Synchronise les utilisateurs et formations depuis LP Core.'

    def handle(self, *args, **options):
        users = sync_users_from_lp_core()
        forms = sync_formations_from_lp_core()
        self.stdout.write(self.style.SUCCESS(
            f"Utilisateurs : {users['created']} créés, {users['updated']} mis à jour. "
            f"Formations : {forms['created']} créées, {forms['updated']} mises à jour."
        ))
        errors = users.get('errors', []) + forms.get('errors', [])
        for err in errors:
            self.stderr.write(err)
