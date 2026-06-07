from django.core.management.base import BaseCommand
from safety_manager.models import RiskFamily, SafetyZone, WorkUnit


RISK_FAMILIES = [
    ('CHUTE_PLAIN_PIED', 'chute de plain-pied', 'Glissade, trébuchement, encombrement, câbles au sol.', 'Sol encombré, rallonge traversante, liquide au sol.', 'Rangement, cheminements, passe-câbles, signalisation.'),
    ('CHUTE_HAUTEUR', 'chute de hauteur', 'Travail sur escabeau, PIRL, plateforme, zone chantier.', 'Travail en hauteur sans stabilité suffisante.', 'Matériel adapté, vérification, formation, interdiction improvisation.'),
    ('MANUTENTION_MANUELLE', 'manutention manuelle', 'Port de charges, postures, efforts.', 'Port d’un équipement lourd seul.', 'Aides mécaniques, binôme, organisation du poste.'),
    ('MANUTENTION_MECANISEE', 'manutention mécanisée', 'Utilisation de chariots ou moyens de levage.', 'Déplacement de charges en zone de circulation.', 'Autorisation, zone balisée, matériel entretenu.'),
    ('CIRCULATION', 'circulation et déplacement', 'Flux élèves, chariots, passages encombrés.', 'Croisement en zone atelier.', 'Plan de circulation, rangement, balisage.'),
    ('CHUTE_OBJETS', 'effondrement / chute d’objets', 'Stockage en hauteur, empilement instable.', 'Matériel posé en équilibre.', 'Rayonnage adapté, charge maximale, rangement.'),
    ('CHIMIQUE', 'risque toxique / chimique', 'Produits, aérosols, colles, solvants, fumées.', 'Produit non étiqueté ou mal stocké.', 'FDS, ventilation, substitution, EPI.'),
    ('INCENDIE_EXPLOSION', 'incendie / explosion', 'Énergie, batteries, produits inflammables.', 'Charge batterie non surveillée.', 'Stockage, extincteurs, procédure, permis feu.'),
    ('BIOLOGIQUE', 'biologique', 'Exposition biologique, hygiène, déchets.', 'Déchets mal gérés.', 'Hygiène, tri, nettoyage.'),
    ('ELECTRIQUE', 'électrique', 'Contact direct/indirect, essais sous tension.', 'Intervention sur platine alimentée.', 'Consignation, VAT, habilitation, EPI/EPC.'),
    ('HYGIENE', 'manque d’hygiène', 'Poste sale, absence nettoyage, déchets.', 'Atelier non rangé après TP.', 'Règles de fin de séance, contrôles.'),
    ('BRUIT', 'bruit', 'Machine bruyante, compresseur, outillage.', 'Exposition répétée sans protection.', 'Réduction source, protections auditives.'),
    ('VIBRATIONS', 'vibrations', 'Outillage vibrant.', 'Utilisation prolongée.', 'Limitation durée, matériel adapté.'),
    ('THERMIQUE', 'ambiances thermiques', 'Chaud/froid, brûlures, locaux.', 'Contact surface chaude.', 'Signalisation, EPI, isolement.'),
    ('LUMINEUSE', 'ambiances lumineuses', 'Éclairage insuffisant ou éblouissement.', 'Travail fin en zone sombre.', 'Éclairage adapté.'),
    ('RAYONNEMENTS', 'rayonnements', 'UV, laser, sources optiques.', 'Essai laser/fibre sans consigne.', 'Consignes, lunettes adaptées, capotage.'),
    ('MACHINES_OUTILS', 'machines et outils', 'Coupure, projection, happement.', 'Perçage sans maintien pièce.', 'Protecteurs, bridage, lunettes, formation.'),
    ('ENTREPRISE_EXT', 'intervention d’entreprise extérieure', 'Coactivité, risques importés/exportés.', 'Intervention prestataire pendant TP.', 'Plan de prévention, balisage, coordination.'),
    ('ORGANISATION', 'organisation du travail', 'Consignes, formation, surcharge, supervision.', 'Activité lancée sans démonstration.', 'Préparation, briefing, validation.'),
    ('AUTRE', 'autre', 'Risque non classé.', '', ''),
]

DEFAULT_ZONES = [
    ('ELEC', 'Atelier électrotechnique', 'atelier'), ('CIEL', 'Zone CIEL', 'atelier'), ('MELEC', 'Zone MELEC', 'atelier'),
    ('MTNE', 'Zone MTNE', 'atelier'), ('CHANTIER', 'Zone chantier pédagogique', 'chantier'), ('MAINT', 'Zone maintenance', 'atelier'),
    ('ECOQ', 'Zone écoquartier', 'extérieur'), ('MAGASIN', 'Magasin outillage', 'stockage'), ('INFO', 'Salle informatique', 'salle'),
    ('STOCK', 'Zone stockage', 'stockage'), ('CIRC', 'Circulations atelier', 'circulation'),
]


class Command(BaseCommand):
    help = 'Crée les familles de risques et zones de base Safety Manager.'

    def handle(self, *args, **options):
        for code, nom, desc, dangers, prev in RISK_FAMILIES:
            RiskFamily.objects.update_or_create(code=code, defaults={
                'nom': nom, 'description': desc, 'exemples_dangers': dangers, 'exemples_prevention': prev, 'actif': True
            })
        for idx, (code, nom, type_zone) in enumerate(DEFAULT_ZONES, start=1):
            zone, _ = SafetyZone.objects.update_or_create(code=code, defaults={'nom': nom, 'type_zone': type_zone, 'ordre_affichage': idx, 'actif': True})
            WorkUnit.objects.get_or_create(code=f'UT-{code}', defaults={'nom': nom, 'zone': zone, 'description': f'Unité de travail initiale : {nom}', 'actif': True})
        self.stdout.write(self.style.SUCCESS(f'Safety Manager initialisé : {RiskFamily.objects.count()} familles, {SafetyZone.objects.count()} zones.'))
