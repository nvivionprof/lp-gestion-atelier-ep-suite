from django.core.management.base import BaseCommand
from decimal import Decimal
from pedashop.models import Article, Emplacement, Magasin, MouvementStock, StockArticleMagasin


class Command(BaseCommand):
    help = 'Crée les magasins et quelques articles de démonstration PedaShop.'

    def handle(self, *args, **options):
        principal, _ = Magasin.objects.get_or_create(code='MAG-ATELIER', defaults={'nom': 'Magasin atelier principal', 'description': 'Magasin consommables principal.'})
        reserve, _ = Magasin.objects.get_or_create(code='MAG-RESERVE', defaults={'nom': 'Magasin réserve', 'description': 'Réserve secondaire / stock tampon.'})
        emp1, _ = Emplacement.objects.get_or_create(magasin=principal, code='A1', defaults={'nom': 'Rayon A1'})
        emp2, _ = Emplacement.objects.get_or_create(magasin=reserve, code='R1', defaults={'nom': 'Réserve R1'})
        articles = [
            ('CONSO-DJ-10A', 'Disjoncteur 10 A courbe C', 'Schneider', 'Protection', 'Disjoncteurs', Decimal('12'), Decimal('5')),
            ('CONSO-PRISE-2P-T', 'Prise 2P+T blanche', 'Legrand', 'Appareillage', 'Prises', Decimal('40'), Decimal('10')),
            ('CONSO-CABLE-R2V-3G15', 'Câble R2V 3G1,5 au mètre', 'Nexans', 'Câble', 'R2V', Decimal('100'), Decimal('25')),
        ]
        for ref, des, fab, cat, sous, stock, mini in articles:
            article, _ = Article.objects.get_or_create(reference_interne=ref, defaults={'designation': des, 'fabricant': fab, 'categorie': cat, 'sous_categorie': sous, 'unite': 'u'})
            stock_obj, created = StockArticleMagasin.objects.get_or_create(article=article, magasin=principal, defaults={'emplacement': emp1, 'stock_reel': stock, 'stock_minimum': mini})
            if created:
                MouvementStock.objects.create(article=article, magasin_destination=principal, emplacement_destination=emp1, type_mouvement='entree_initiale', quantite=stock, stock_avant=0, stock_apres=stock, commentaire='Données de démonstration PedaShop')
        StockArticleMagasin.objects.get_or_create(article=Article.objects.get(reference_interne='CONSO-DJ-10A'), magasin=reserve, defaults={'emplacement': emp2, 'stock_reel': Decimal('30'), 'stock_minimum': Decimal('10')})
        self.stdout.write(self.style.SUCCESS('Données de base PedaShop créées.'))
