from django.core.management.base import BaseCommand
from pedashop.sync import sync_users_from_lp_core


class Command(BaseCommand):
    help = 'Synchronise les utilisateurs LP Core vers PedaShop.'

    def handle(self, *args, **options):
        report = sync_users_from_lp_core()
        self.stdout.write(self.style.SUCCESS(f"Synchronisation PedaShop terminée : {report}"))
