from django.core.management.base import BaseCommand
from pedashop.models import StockArticleMagasin
from pedashop.services import recalculate_stock_alerts


class Command(BaseCommand):
    help = 'Contrôle simple de cohérence des stocks PedaShop.'

    def handle(self, *args, **options):
        recalculate_stock_alerts()
        warnings = []
        errors = []
        for stock in StockArticleMagasin.objects.select_related('article', 'magasin'):
            if stock.stock_disponible < 0:
                errors.append(f'{stock.article.reference_interne} / {stock.magasin.code} : disponible négatif')
            detail = stock.qte_ok + stock.qte_use + stock.stock_hs
            if detail and detail != stock.stock_reel:
                warnings.append(f'{stock.article.reference_interne} / {stock.magasin.code} : détail OK+Usé+HS différent du stock réel')
        for w in warnings:
            self.stdout.write(self.style.WARNING(w))
        if errors:
            for e in errors:
                self.stderr.write(e)
            raise SystemExit(1)
        self.stdout.write(self.style.SUCCESS('Contrôle PedaShop OK.'))
