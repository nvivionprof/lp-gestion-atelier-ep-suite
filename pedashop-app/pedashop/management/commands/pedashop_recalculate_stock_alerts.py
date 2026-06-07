from django.core.management.base import BaseCommand
from pedashop.services import recalculate_stock_alerts


class Command(BaseCommand):
    help = 'Recalcule toutes les alertes de stock PedaShop.'

    def handle(self, *args, **options):
        count = recalculate_stock_alerts()
        self.stdout.write(self.style.SUCCESS(f'{count} stocks recalculés.'))
