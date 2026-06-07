from django.core.management.base import BaseCommand
from inventory.models import Competence, CompetenceMapping, Formation, Person


FORMATIONS = {
    'BAC_CIEL': ('Bac Pro CIEL', 'Bac Pro CIEL'),
    'BAC_MELEC': ('Bac Pro MELEC', 'Bac Pro MELEC'),
    'CAP_ELEC': ('CAP Pro Électricité', 'CAP Pro Électricité — dérivé MELEC'),
    'BTS_ET': ('BTS Électrotechnique', 'BTS Électrotechnique'),
    'BTS_FED': ('BTS Fluides Énergies Domotique', 'BTS FED'),
}

COMPETENCES = {
    'BAC_CIEL': [
        ('C01', 'Communiquer en situation professionnelle', 'Bloc 3', 'U32'),
        ('C03', 'Participer à un projet', 'Bloc 1', 'U2'),
        ('C04', 'Analyser une structure matérielle et logicielle', 'Bloc 3', 'U32'),
        ('C06', 'Valider la conformité d’une installation', 'Bloc 2', 'U31'),
        ('C07', 'Réaliser des maquettes et prototypes', 'Bloc 1', 'U2'),
        ('C08', 'Coder', 'Bloc 3', 'U32'),
        ('C09', 'Installer les éléments d’un système électronique ou informatique', 'Bloc 2', 'U31'),
        ('C10', 'Exploiter un réseau informatique', 'Bloc 2', 'U31'),
        ('C11', 'Maintenir un système électronique ou réseau informatique', 'Bloc 1', 'U2'),
    ],
    'BTS_ET': [
        ('C1', 'Recenser et prendre en compte les normes et réglementations applicables', 'Conduite de projet/chantier', 'U52'),
        ('C2', 'Extraire les informations nécessaires à la réalisation des tâches', 'Analyse diagnostic maintenance', 'U51'),
        ('C3', 'Gérer les risques et les aléas liés à la réalisation des tâches', 'Conduite de projet/chantier', 'U52'),
        ('C4', 'Communiquer de manière adaptée à l’oral et à l’écrit', 'Transversal', 'U62'),
        ('C11', 'Réaliser les documents techniques du projet/chantier', 'Conception détaillée', 'U61'),
        ('C12', 'Gérer et conduire le projet/chantier', 'Conduite de projet/chantier', 'U52'),
        ('C13', 'Mesurer les grandeurs caractéristiques', 'Analyse diagnostic maintenance', 'U51'),
        ('C16', 'Appliquer un protocole de mise en service', 'Réalisation mise en service', 'U62'),
        ('C17', 'Réaliser un diagnostic de performance, de sécurité', 'Analyse diagnostic maintenance', 'U51'),
        ('C18', 'Réaliser des opérations de maintenance', 'Analyse diagnostic maintenance', 'U51'),
    ],
    'BTS_FED': [
        ('C2', 'Analyser un système', 'Concevoir et définir', ''),
        ('C5', 'Appliquer les réglementations en vigueur', 'Concevoir et définir', ''),
        ('C7', 'Réaliser des essais, des mesures', 'Mettre en service - optimiser', ''),
        ('C8', 'Vérifier, adapter les performances d’un système', 'Mettre en service - optimiser', ''),
        ('C10', 'Organiser et suivre le projet, animer une équipe', 'Conduire un projet', ''),
        ('C11', 'Établir et mettre à jour un planning', 'Communiquer', ''),
        ('C12', 'Recueillir et traiter l’information', 'Communiquer', ''),
        ('C13', 'Écouter, dialoguer, argumenter', 'Communiquer', ''),
        ('C14', 'Élaborer et utiliser un support de communication', 'Communiquer', ''),
    ],
    'BAC_MELEC': [
        ('MELEC-PREP', 'Préparer les opérations', 'Préparation', ''),
        ('MELEC-REAL', 'Réaliser une installation ou une intervention', 'Réalisation', ''),
        ('MELEC-MES', 'Mettre en service et contrôler', 'Mise en service', ''),
        ('MELEC-MAINT', 'Réaliser une opération de maintenance', 'Maintenance', ''),
        ('MELEC-COM', 'Communiquer et rendre compte', 'Communication', ''),
    ],
    'CAP_ELEC': [
        ('CAP-PREP', 'Préparer une opération', 'Préparation', ''),
        ('CAP-REAL', 'Réaliser une installation simple', 'Réalisation', ''),
        ('CAP-MES', 'Contrôler et mettre en service', 'Mise en service', ''),
        ('CAP-COM', 'Communiquer et rendre compte', 'Communication', ''),
    ],
}

# action_type, role, competence codes, criterion
MAPPINGS = {
    'BAC_CIEL': [
        ('checkout', 'user', ['C01', 'C03'], 'Demande de sortie et respect de la procédure'),
        ('inventory_out', 'user', ['C01', 'C06'], 'Inventaire de sortie renseigné'),
        ('inventory_return', 'user', ['C01', 'C06', 'C11'], 'Inventaire de retour et anomalie éventuelle'),
        ('checkout', 'storekeeper', ['C01', 'C03', 'C06'], 'Sortie validée avec identification emprunteur/matériel'),
        ('return', 'storekeeper', ['C01', 'C06', 'C11'], 'Retour contrôlé et tracé'),
        ('inventory_out', 'storekeeper', ['C06'], 'Contrôle de conformité en sortie'),
        ('inventory_return', 'storekeeper', ['C06', 'C11'], 'Contrôle de conformité en retour'),
    ],
    'BTS_ET': [
        ('checkout', 'user', ['C2', 'C3', 'C4'], 'Préparation et traçabilité de l’outillage'),
        ('inventory_out', 'user', ['C2', 'C13', 'C16'], 'Contrôle d’un appareil ou kit'),
        ('inventory_return', 'user', ['C4', 'C17'], 'Signalement d’écart ou anomalie'),
        ('checkout', 'storekeeper', ['C2', 'C3', 'C12'], 'Organisation de sortie de matériel'),
        ('return', 'storekeeper', ['C3', 'C4', 'C17', 'C18'], 'Retour, anomalie, maintenance'),
    ],
    'BTS_FED': [
        ('checkout', 'user', ['C12', 'C13'], 'Recueil et transmission d’information'),
        ('inventory_out', 'user', ['C2', 'C7'], 'Analyse d’un système / appareil de mesure'),
        ('inventory_return', 'user', ['C7', 'C8', 'C13'], 'Contrôle retour et argumentation'),
        ('checkout', 'storekeeper', ['C10', 'C11', 'C12'], 'Organisation et suivi des moyens'),
        ('return', 'storekeeper', ['C8', 'C10', 'C12', 'C13'], 'Suivi, aléas et communication'),
    ],
    'BAC_MELEC': [
        ('checkout', 'user', ['MELEC-PREP', 'MELEC-COM'], 'Préparation de l’outillage'),
        ('inventory_out', 'user', ['MELEC-PREP', 'MELEC-MES'], 'Contrôle avant intervention'),
        ('inventory_return', 'user', ['MELEC-MAINT', 'MELEC-COM'], 'Retour et anomalie'),
        ('checkout', 'storekeeper', ['MELEC-PREP', 'MELEC-COM'], 'Sortie tracée'),
        ('return', 'storekeeper', ['MELEC-MAINT', 'MELEC-COM'], 'Retour tracé et maintenance'),
    ],
    'CAP_ELEC': [
        ('checkout', 'user', ['CAP-PREP', 'CAP-COM'], 'Préparation du matériel'),
        ('inventory_out', 'user', ['CAP-PREP', 'CAP-MES'], 'Contrôle simple'),
        ('inventory_return', 'user', ['CAP-MES', 'CAP-COM'], 'Retour et compte rendu'),
        ('checkout', 'storekeeper', ['CAP-PREP', 'CAP-COM'], 'Sortie tracée'),
        ('return', 'storekeeper', ['CAP-MES', 'CAP-COM'], 'Retour tracé'),
    ],
}

class Command(BaseCommand):
    help = 'Crée les compétences référentielles et les correspondances actions-compétences ToolMag.'

    def handle(self, *args, **options):
        formation_objs = {}
        for code, (name, ref) in FORMATIONS.items():
            formation_objs[code], _ = Formation.objects.get_or_create(code=code, defaults={'name': name, 'referential_name': ref})
        comp_objs = {}
        for fcode, comps in COMPETENCES.items():
            formation = formation_objs[fcode]
            for code, title, block, unit in comps:
                comp, _ = Competence.objects.update_or_create(
                    formation=formation,
                    code=code,
                    defaults={'title': title, 'block': block, 'unit': unit, 'active': True},
                )
                comp_objs[(fcode, code)] = comp
        created = 0
        for fcode, mappings in MAPPINGS.items():
            formation = formation_objs[fcode]
            for action_type, role, codes, criterion in mappings:
                for code in codes:
                    comp = comp_objs[(fcode, code)]
                    _, was_created = CompetenceMapping.objects.update_or_create(
                        formation=formation,
                        action_type=action_type,
                        role=role,
                        competence=comp,
                        defaults={'criterion': criterion, 'weight': 1, 'active': True},
                    )
                    created += int(was_created)
        self.stdout.write(self.style.SUCCESS(f'Référentiels ToolMag créés/mis à jour. Nouvelles correspondances : {created}.'))
