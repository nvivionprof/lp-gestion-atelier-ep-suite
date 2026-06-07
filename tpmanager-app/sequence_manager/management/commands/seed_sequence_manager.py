from django.core.management.base import BaseCommand
from sequence_manager.models import SeqColoration, SeqWeeklySlot, SeqZone, SeqRotationBlock, SeqRotationFormation
from tp_manager.models import SystemePedagogiqueRef, TpUser


class Command(BaseCommand):
    help = 'Initialise les paramètres de base de Sequence Manager.'

    def handle(self, *args, **options):
        colorations = [
            ('AUC', 'Aucune', '#64748b'), ('TC', 'Tronc commun', '#0f766e'), ('SB', 'Smart Building', '#2563eb'),
            ('RES', 'Monteur réseau', '#7c3aed'), ('REPELEC', 'Réparateur électronique', '#ea580c'),
            ('GTB', 'GTB / bâtiment communicant', '#0891b2'), ('ENE', 'Énergie', '#16a34a'),
            ('MES', 'Mesures / qualité énergie', '#ca8a04'), ('DOM', 'Domotique', '#db2777'),
        ]
        for code, nom, couleur in colorations:
            SeqColoration.objects.update_or_create(code=code, defaults={'nom': nom, 'couleur': couleur, 'active': True})
        for day, half in [(2,'AM'), (4,'PM'), (5,'PM')]:
            SeqWeeklySlot.objects.get_or_create(day=day, half_day=half)
        zones = [
            ('GTB', 'Zone GTB / Domotique'), ('RES', 'Zone réseau'), ('SYS', 'Zone systèmes'), ('CHANT', 'Zone chantier'), ('MES', 'Zone mesures'),
        ]
        for code, nom in zones:
            z, _ = SeqZone.objects.update_or_create(code=code, defaults={'nom': nom, 'active': True})
            for sys in SystemePedagogiqueRef.objects.filter(zone_code__icontains=code)[:20]:
                z.systemes.add(sys)
        block, _ = SeqRotationBlock.objects.update_or_create(code='BLOC_TERM', defaults={'nom': 'Bloc TERM', 'description': 'Bloc exemple multi-formations terminales / BTS.', 'active': True})
        block.slots.set(SeqWeeklySlot.objects.filter(code__in=['MAR_AM','JEU_PM','VEN_PM']))
        block.zones.set(SeqZone.objects.filter(code__in=['GTB','RES','SYS','MES']))
        block.professeurs.set(TpUser.objects.filter(active=True, role_principal__in=['professeur','admin','responsable'])[:10])
        for formation, classe, niveau, effectif in [('MELEC','TMELEC','Terminale',6), ('CIEL','TCIEL','Terminale',4), ('FED','FED2','2ème année',2), ('STEL','STEL2','2ème année',4)]:
            SeqRotationFormation.objects.update_or_create(block=block, formation_code=formation, classe=classe, defaults={'niveau': niveau, 'effectif_prevu': effectif})
        self.stdout.write(self.style.SUCCESS('Sequence Manager initialisé.'))
