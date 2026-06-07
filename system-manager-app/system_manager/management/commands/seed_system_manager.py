from django.core.management.base import BaseCommand
from system_manager.models import Formation, Niveau, WorkshopZone, WorkshopSubZone, DocumentCategory


class Command(BaseCommand):
    help = 'Initialise les référentiels de base du module System Manager.'

    def handle(self, *args, **options):
        formations = [
            ('CIEL', 'Bac Pro CIEL'), ('MELEC', 'Bac Pro MELEC'), ('MTNE', '2de MTNE'), ('ELEC', 'CAP électricien'),
            ('FED', 'BTS FED'), ('STEL', 'BTS électrotechnique / STEL'),
        ]
        for code, nom in formations:
            Formation.objects.get_or_create(code=code, defaults={'nom': nom})
        niveaux = [('CAP1', 'CAP 1re année', 10), ('CAP2', 'CAP 2e année', 20), ('2DE', 'Seconde', 30), ('1RE', 'Première', 40), ('TLE', 'Terminale', 50), ('BTS1', 'BTS 1re année', 60), ('BTS2', 'BTS 2e année', 70)]
        for code, nom, ordre in niveaux:
            Niveau.objects.get_or_create(code=code, defaults={'nom': nom, 'ordre': ordre})
        zones = [('FORM', 'Pôle formation'), ('MAINT', 'Pôle maintenance / mise en service'), ('ECOQ', 'Éco-quartier'), ('INT', 'Intégration / réseaux'), ('CHA', 'Chantier pédagogique')]
        for idx, (code, nom) in enumerate(zones, start=1):
            WorkshopZone.objects.get_or_create(code=code, defaults={'nom': nom, 'ordre_affichage': idx*10})
        for zone_code, code, nom in [('FORM', 'GEN', 'Zone générale'), ('MAINT', 'MES', 'Mise en service'), ('INT', 'BAIE', 'Baies et réseaux'), ('ECOQ', 'GTB', 'GTB / supervision')]:
            zone = WorkshopZone.objects.filter(code=zone_code).first()
            if zone:
                WorkshopSubZone.objects.get_or_create(zone=zone, code=code, defaults={'nom': nom})
        cats = [
            ('01_PRESENTATION', '01 - Présentation du système'), ('02_DOC_CONSTRUCTEUR', '02 - Documentation constructeur'),
            ('03_PLANS_ELEC', '03 - Plans électriques'), ('04_PLANS_RESEAUX', '04 - Plans fluidiques / réseaux / implantation'),
            ('05_ANALYSE_FONCTIONNELLE', '05 - Analyse fonctionnelle'), ('06_MISE_EN_SERVICE', '06 - Procédure de mise en service'),
            ('07_ARRET', '07 - Procédure d’arrêt'), ('08_SECURITE', '08 - Sécurité / risques / consignation'),
            ('09_PRISE_POSTE', '09 - Fiche de prise de poste'), ('10_TP', '10 - TP associés'),
            ('11_MAINTENANCE', '11 - Maintenance / dépannage'), ('12_HISTORIQUE', '12 - Historique des modifications'),
        ]
        for idx, (code, nom) in enumerate(cats, start=1):
            DocumentCategory.objects.get_or_create(code=code, defaults={'nom': nom, 'ordre': idx*10})
        self.stdout.write(self.style.SUCCESS('Référentiels System Manager initialisés.'))
