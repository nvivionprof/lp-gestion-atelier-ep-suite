from django.core.management.base import BaseCommand
from tp_manager.models import (
    Formation, Niveau, FormationNiveau, ZoneApprentissage, ThemeGeneral, ThemeSecondaire, TypeTP,
    Referentiel, BlocCompetence, Competence, SousCompetence, ActiviteReferentiel, TacheReferentiel,
    PoleActivite, UniteCertificative, BlocUnite, SavoirAssocie, CompetenceSavoir, CritereEvaluation, IndicateurEvaluation, TacheCompetence,
    TP, TPCompetence, TPTache, TPSavoir, TPCritere
)


class Command(BaseCommand):
    help = 'Initialise les listes de base TP Manager et quelques référentiels simplifiés.'

    def handle(self, *args, **options):
        niveaux = [
            ('2NDE', '2nde', 10), ('1ERE', '1ère', 20), ('TERM', 'Terminale', 30),
            ('CAP1', 'CAP 1re année', 10), ('CAP2', 'CAP 2e année', 20),
            ('BTS1', 'BTS 1re année', 10), ('BTS2', 'BTS 2e année', 20),
        ]
        for code, nom, ordre in niveaux:
            Niveau.objects.get_or_create(code=code, defaults={'nom': nom, 'ordre': ordre})
        formations = [
            ('MTNE', 'Bac Pro MTNE'), ('CIEL', 'Bac Pro CIEL'), ('MELEC', 'Bac Pro MELEC'), ('MFER', 'Bac Pro MFER'),
            ('CAP_ELEC', 'CAP Électricien'), ('BTS_FED', 'BTS FED'), ('BTS_ELEC', 'BTS Électrotechnique'),
        ]
        for code, nom in formations:
            Formation.objects.get_or_create(code=code, defaults={'nom': nom})
        allowed = {
            'MTNE': ['2NDE'], 'CIEL': ['2NDE', '1ERE', 'TERM'], 'MELEC': ['2NDE', '1ERE', 'TERM'], 'MFER': ['2NDE', '1ERE', 'TERM'],
            'CAP_ELEC': ['CAP1', 'CAP2'], 'BTS_FED': ['BTS1', 'BTS2'], 'BTS_ELEC': ['BTS1', 'BTS2'],
        }
        for fcode, ncodes in allowed.items():
            f = Formation.objects.filter(code=fcode).first()
            for ncode in ncodes:
                n = Niveau.objects.filter(code=ncode).first()
                if f and n:
                    FormationNiveau.objects.get_or_create(formation=f, niveau=n)
        for code, nom in [('FORM', 'Pôle formation'), ('MAINT', 'Pôle maintenance'), ('MES', 'Mise en service'), ('ECQU', 'Écoquartier'), ('INT', 'Intégration'), ('CHA', 'Chantier')]:
            ZoneApprentissage.objects.get_or_create(code=code, defaults={'nom': nom})
        for code, nom in [('BAT', 'Bâtiment'), ('TER', 'Tertiaire'), ('INFO', 'Informatique / réseaux'), ('IND', 'Industriel'), ('PART', 'Particulier / entreprise')]:
            ThemeGeneral.objects.get_or_create(code=code, defaults={'nom': nom})
        tg_bat = ThemeGeneral.objects.filter(code='BAT').first()
        tg_info = ThemeGeneral.objects.filter(code='INFO').first()
        for code, nom, tg in [('SSI', 'Sécurité incendie', tg_bat), ('GTB', 'GTB / supervision', tg_bat), ('ECL', 'Éclairage', tg_bat), ('CTA', 'CTA / ventilation', tg_bat), ('PAC', 'Pompe à chaleur', tg_bat), ('RES', 'Réseaux informatiques', tg_info), ('CYB', 'Cybersécurité', tg_info)]:
            ThemeSecondaire.objects.get_or_create(code=code, defaults={'nom': nom, 'theme_general': tg})
        for code, nom in [('GUIDE', 'TP guidé'), ('DECOUVERTE', 'TP découverte'), ('DIAG', 'Diagnostic'), ('MAINT', 'Maintenance'), ('MES', 'Mise en service'), ('CABLAGE', 'Câblage'), ('PROG', 'Programmation'), ('MESURE', 'Mesure'), ('DOC', 'Étude documentaire'), ('EVAL', 'Évaluation')]:
            TypeTP.objects.get_or_create(code=code, defaults={'nom': nom})
        self.seed_simple_competences()
        self.seed_official_structures_and_demo_tps()
        self.stdout.write(self.style.SUCCESS('TP Manager initialisé.'))

    def seed_simple_competences(self):
        data = {
            'BTS_FED': [('A', 'Concevoir et définir', [('C1', 'Analyser les besoins d’un client'), ('C2', 'Analyser un système'), ('C3', 'Concevoir des solutions technologiques'), ('C4', 'Décoder et élaborer des plans et des schémas'), ('C5', 'Appliquer les règlementations en vigueur')]), ('B', 'Mettre en service - optimiser', [('C6', 'Mettre en œuvre des outils de pilotage'), ('C7', 'Réaliser des essais, des mesures'), ('C8', 'Vérifier, adapter les performances d’un système')]), ('C', 'Conduire un projet', [('C9', 'Déterminer des prix ou des coûts'), ('C10', 'Organiser et suivre le projet')]), ('D', 'Communiquer', [('C11', 'Établir et mettre à jour un planning'), ('C12', 'Recueillir et traiter l’information'), ('C13', 'Écouter, dialoguer, argumenter'), ('C14', 'Élaborer et utiliser un support de communication')])],
            'BTS_ELEC': [('PRELIM', 'Conception - étude préliminaire', [('C5', 'Interpréter un besoin client/utilisateur'), ('C6', 'Modéliser le comportement'), ('C8', 'Dimensionner les constituants'), ('C10', 'Proposer l’architecture')]), ('REAL', 'Réalisation, mise en service', [('C14', 'Réaliser un ouvrage, une installation ou un équipement'), ('C15', 'Configurer et programmer'), ('C16', 'Mettre en service')]), ('MAINT', 'Analyse, diagnostic, maintenance', [('C13', 'Mesurer les grandeurs caractéristiques'), ('C17', 'Réaliser un diagnostic'), ('C18', 'Réaliser des opérations de maintenance')])],
            'CIEL': [('B1', 'Réalisation et maintenance de produits électroniques', [('B1P', 'Participer à un projet'), ('B1M', 'Maintenir un système électronique ou réseau informatique')]), ('B2', 'Mise en œuvre de réseaux informatiques', [('B2V', 'Valider la conformité d’une installation'), ('B2I', 'Installer les éléments d’un système'), ('B2E', 'Exploiter un réseau informatique')]), ('B3', 'Valorisation de la donnée et cybersécurité', [('B3C', 'Communiquer en situation professionnelle'), ('B3A', 'Analyser une structure matérielle et logicielle'), ('B3D', 'Coder')])],
            'MELEC': [('A1', 'Préparation des opérations', [('C1', 'Analyser les conditions de l’opération'), ('C2', 'Analyser et exploiter les données techniques'), ('C3', 'Choisir les matériels, équipements et outillages')]), ('A2', 'Réalisation', [('C4', 'Organiser son poste de travail'), ('C5', 'Implanter, poser, installer'), ('C6', 'Câbler, raccorder')]), ('A3', 'Mise en service', [('C7', 'Réaliser les vérifications, réglages, essais'), ('C8', 'Participer à la réception technique')]), ('A4', 'Maintenance', [('C9', 'Réaliser une opération de maintenance préventive'), ('C10', 'Réaliser une opération de dépannage')])],
            'MFER': [('P1', 'Préparation', [('C1', 'Analyser les conditions de l’opération'), ('C2', 'Analyser les données techniques'), ('C3', 'Choisir matériels et outillages')]), ('P2', 'Réalisation et mise en service', [('C4', 'Organiser et sécuriser son intervention'), ('C5', 'Réaliser une installation'), ('C6', 'Mettre en service une installation')]), ('P3', 'Maintenance', [('C7', 'Réaliser la maintenance préventive'), ('C8', 'Réaliser la maintenance corrective')])],
            'CAP_ELEC': [('P1', 'Réalisation d’une installation', [('C1', 'Repérer les conditions de l’opération'), ('C2', 'Organiser l’opération'), ('C3', 'Réaliser une installation')]), ('P2', 'Mise en service', [('C4', 'Contrôler les grandeurs caractéristiques'), ('C5', 'Valider le fonctionnement')]), ('P3', 'Maintenance', [('C6', 'Remplacer un matériel électrique'), ('C7', 'Communiquer avec le client/usager')])],
        }
        for fcode, blocs in data.items():
            formation = Formation.objects.filter(code=fcode).first()
            if not formation:
                continue
            ref, _ = Referentiel.objects.get_or_create(formation=formation, nom=f'Référentiel simplifié {formation.code}', defaults={'version': 'préchargement V0'})
            for b_order, (bcode, blib, comps) in enumerate(blocs, start=1):
                bloc, _ = BlocCompetence.objects.get_or_create(referentiel=ref, code=bcode, defaults={'libelle': blib, 'ordre': b_order})
                for c_order, (ccode, clib) in enumerate(comps, start=1):
                    Competence.objects.get_or_create(bloc=bloc, code=ccode, defaults={'libelle': clib, 'ordre': c_order})


    def seed_official_structures_and_demo_tps(self):
        """Précharge une base démo exploitable pour tester TP Manager.
        Les libellés reprennent les appellations officielles principales, tout en
        restant volontairement synthétiques pour ne pas remplacer l'import complet
        des référentiels PDF.
        """
        official = {
            'CAP_ELEC': {
                'ref': ('Référentiel CAP Électricien', 'officiel - structure synthétique'),
                'poles': [('P1', 'Réalisation d’une installation'), ('P2', 'Mise en service d’une installation'), ('P3', 'Maintenance d’une installation')],
                'unites': [('UP1', 'Réalisation d’une installation'), ('UP2', 'Mise en service d’une installation'), ('UP3', 'Maintenance d’une installation')],
                'activites': [('A1', 'Préparation des opérations de réalisation, de mise en service, de maintenance'), ('A2', 'Réalisation'), ('A3', 'Mise en service'), ('A4', 'Maintenance'), ('A5', 'Communication')],
                'taches': [('A1','TA 1-1','Prendre connaissance du dossier relatif aux opérations à réaliser dans leur environnement'), ('A2','TA 2-2','Implanter, poser, installer les matériels électriques'), ('A2','TA 2-3','Câbler, raccorder les matériels électriques'), ('A3','TA 3-1','Réaliser les vérifications, les réglages et les essais fonctionnels')],
                'blocks': [('B1','Réalisation d’une installation','UP1'), ('B2','Mise en service d’une installation','UP2'), ('B3','Maintenance d’une installation','UP3')],
                'competences': [('B1','CO1','Repérer les conditions de l’opération et son contexte'), ('B1','CO2','Organiser l’opération dans son contexte'), ('B1','CO3','Réaliser une installation de manière écoresponsable'), ('B2','CO4','Contrôler les grandeurs caractéristiques de l’installation'), ('B2','CO5','Valider le fonctionnement de l’installation'), ('B3','CO6','Remplacer un matériel électrique')],
            },
            'CIEL': {
                'ref': ('Référentiel Bac Pro CIEL', '2023 - structure synthétique'),
                'poles': [('E', 'Réalisation et maintenance de produits électroniques'), ('R', 'Mise en œuvre de réseaux informatiques'), ('D', 'Valorisation de la donnée et cybersécurité')],
                'unites': [('U2','Réalisation et maintenance de produits électroniques'), ('U31','Mise en œuvre de réseaux informatiques'), ('U32','Valorisation de la donnée et cybersécurité')],
                'activites': [('E1','Étude et conception de produits électroniques'), ('E4','Intégration matérielle et logicielle'), ('R2','Installation et qualification'), ('R3','Exploitation et maintien en condition opérationnelle'), ('D2','Développement et validation de solutions logicielles')],
                'taches': [('E1','T1','Analyse et saisie d’un schéma ou étude d’un système électronique communicant'), ('R2','T1','Installer et qualifier une infrastructure réseau'), ('R3','T1','Exploiter et maintenir un réseau informatique'), ('D2','T1','Coder et valider une solution logicielle')],
                'blocks': [('B1','Réalisation et maintenance de produits électroniques','U2'), ('B2','Mise en œuvre de réseaux informatiques','U31'), ('B3','Valorisation de la donnée et cybersécurité','U32')],
                'competences': [('B1','C03','Participer à un projet'), ('B1','C07','Réaliser des maquettes et prototypes'), ('B2','C06','Valider la conformité d’une installation'), ('B2','C09','Installer les éléments d’un système électronique ou informatique'), ('B2','C10','Exploiter un réseau informatique'), ('B3','C01','Communiquer en situation professionnelle français/anglais'), ('B3','C04','Analyser une structure matérielle et logicielle'), ('B3','C08','Coder')],
            },
            'MFER': {
                'ref': ('Référentiel Bac Pro MFER', '2021 - structure synthétique'),
                'poles': [('P1','Préparation des opérations à réaliser'), ('P2','Réalisation et mise en service d’une installation'), ('P3','Maintenance d’une installation')],
                'unites': [('U2','Préparation d’une intervention'), ('U31','Réalisation et mise en service d’une installation'), ('U32','Maintenance d’une installation')],
                'activites': [('A1','Préparation des opérations à réaliser'), ('A2','Réalisation'), ('A3','Mise en service'), ('A4','Maintenance'), ('A5','Communication')],
                'taches': [('A1','A1T1','Prendre connaissance des dossiers relatifs aux opérations à réaliser'), ('A1','A1T3','Analyser les risques relatifs aux opérations à réaliser'), ('A2','A2T4','Câbler, raccorder les équipements électriques'), ('A3','A3T2','Réaliser la mise en service de l’installation'), ('A4','A4T2','Réaliser une opération de maintenance corrective')],
                'blocks': [('B1','Préparation d’une intervention','U2'), ('B2','Réalisation et mise en service d’une installation','U31'), ('B3','Maintenance d’une installation','U32')],
                'competences': [('B1','C1','Analyser les conditions de l’opération et son contexte'), ('B1','C2','Analyser et exploiter les données techniques de l’intervention'), ('B2','C4','Organiser et sécuriser son intervention'), ('B2','C7','Mettre en service une installation'), ('B2','C8','Contrôler, régler et paramétrer l’installation'), ('B3','C9','Réaliser des opérations de maintenance préventive'), ('B3','C10','Réaliser des opérations de maintenance corrective')],
            },
            'BTS_FED': {
                'ref': ('Référentiel BTS FED', '2014 - structure synthétique'),
                'poles': [('ETUDE','Étude'), ('PREPA','Préparation'), ('EXEC','Exécution'), ('CLIENT','Relation client'), ('COM','Communication')],
                'unites': [('U41','Analyse et définition d’un système'), ('U42','Physique-chimie associée'), ('U5','Intervention sur système'), ('U61','Conduite de projet'), ('U62','Rapport d’activités')],
                'activites': [('ETUDE','Étude technique'), ('INTERV','Intervention'), ('ORG','Organisation'), ('COM','Communication')],
                'taches': [('ETUDE','T1','Analyser le CCTP ou le cahier des charges'), ('ETUDE','T4','Concevoir et définir l’installation'), ('INTERV','T15','Réaliser la mise en service d’une installation'), ('ORG','T18','Participer au suivi et à la gestion du chantier')],
                'blocks': [('A','Concevoir et définir','U41'), ('B','Mettre en service - optimiser','U5'), ('C','Conduire un projet','U61'), ('D','Communiquer','U62')],
                'competences': [('A','C1','Analyser les besoins d’un client'), ('A','C2','Analyser un système'), ('A','C4','Décoder et élaborer des plans et des schémas'), ('B','C7','Réaliser des essais, des mesures'), ('B','C8','Vérifier, adapter les performances d’un système'), ('C','C10','Organiser et suivre le projet'), ('D','C12','Recueillir et traiter l’information')],
            },
            'BTS_ELEC': {
                'ref': ('Référentiel BTS Électrotechnique', '2020 - structure synthétique'),
                'poles': [('P1','Conception - étude préliminaire'), ('P2','Conception - étude détaillée du projet'), ('P3','Conduite de projet/chantier'), ('P4','Réalisation, mise en service d’un projet'), ('P5','Analyse, diagnostic, maintenance')],
                'unites': [('U4','Conception - étude préliminaire'), ('U51','Analyse, diagnostic, maintenance'), ('U52','Conduite de projet/chantier'), ('U61','Conception - étude détaillée du projet'), ('U62','Réalisation, mise en service d’un projet')],
                'activites': [('A1','Conception - étude préliminaire'), ('A2','Conception - étude détaillée du projet'), ('A3','Analyse - diagnostic'), ('A4','Maintenance'), ('A5','Conduite de projet/chantier'), ('A6','Réalisation : installation - intégration'), ('A7','Mise en service')],
                'taches': [('A1','T 1.1','Analyser et/ou élaborer les documents relatifs aux besoins du client/utilisateur'), ('A1','T 1.3','Dimensionner les constituants de l’installation'), ('A3','T 3.2','Mesurer et contrôler l’installation, exploiter les mesures pour faire le diagnostic'), ('A6','T 6.2','Implanter, poser, installer, câbler, raccorder les matériels électriques'), ('A7','T 7.1','Réaliser les contrôles, configurations et essais fonctionnels')],
                'blocks': [('B4','Conception - étude préliminaire','U4'), ('B51','Analyse, diagnostic, maintenance','U51'), ('B52','Conduite de projet/chantier','U52'), ('B61','Conception - étude détaillée du projet','U61'), ('B62','Réalisation, mise en service d’un projet','U62')],
                'competences': [('B52','C1','Recenser et prendre en compte les normes et réglementations'), ('B51','C2','Extraire les informations nécessaires à la réalisation des tâches'), ('B62','C4','Communiquer de manière adaptée'), ('B4','C5','Interpréter un besoin client/utilisateur, un CCTP, un cahier des charges'), ('B4','C8','Dimensionner les constituants'), ('B61','C11','Réaliser les documents du projet/chantier'), ('B51','C13','Mesurer les grandeurs caractéristiques'), ('B62','C14','Réaliser un ouvrage, une installation, un équipement électrique'), ('B62','C16','Appliquer un protocole de mise en service'), ('B51','C18','Réaliser des opérations de maintenance')],
            },
        }
        for fcode, cfg in official.items():
            formation = Formation.objects.filter(code=fcode).first()
            if not formation:
                continue
            ref, _ = Referentiel.objects.get_or_create(formation=formation, nom=cfg['ref'][0], defaults={'version': cfg['ref'][1], 'source': 'Préchargement TP Manager V2.7.1'})
            act_map = {}
            bloc_map = {}
            comp_map = {}
            unite_map = {}
            for order, (code, lib) in enumerate(cfg['poles'], 1):
                PoleActivite.objects.get_or_create(referentiel=ref, code=code, defaults={'libelle': lib, 'ordre': order})
            for order, (code, lib) in enumerate(cfg['unites'], 1):
                unite_map[code], _ = UniteCertificative.objects.get_or_create(referentiel=ref, code=code, defaults={'libelle': lib, 'ordre': order})
            for order, (code, lib) in enumerate(cfg['activites'], 1):
                act_map[code], _ = ActiviteReferentiel.objects.get_or_create(referentiel=ref, code=code, defaults={'libelle': lib, 'ordre': order})
            for order, (act_code, code, lib) in enumerate(cfg['taches'], 1):
                act = act_map.get(act_code) or next(iter(act_map.values()), None)
                if act:
                    TacheReferentiel.objects.get_or_create(activite=act, code=code, defaults={'libelle': lib, 'ordre': order})
            for order, (code, lib, ucode) in enumerate(cfg['blocks'], 1):
                bloc_map[code], _ = BlocCompetence.objects.get_or_create(referentiel=ref, code=code, defaults={'libelle': lib, 'unite': ucode, 'ordre': order})
                if ucode in unite_map:
                    BlocUnite.objects.get_or_create(bloc=bloc_map[code], unite=unite_map[ucode])
            for order, (bcode, ccode, clib) in enumerate(cfg['competences'], 1):
                bloc = bloc_map.get(bcode)
                if bloc:
                    comp_map[ccode], _ = Competence.objects.get_or_create(bloc=bloc, code=ccode, defaults={'libelle': clib, 'ordre': order})
                    crit, _ = CritereEvaluation.objects.get_or_create(competence=comp_map[ccode], code=f'{ccode}-OBS', defaults={'libelle': f'Les attendus liés à {ccode} sont observables et correctement justifiés.', 'ordre': 1})
                    IndicateurEvaluation.objects.get_or_create(critere=crit, libelle='Travail conforme aux consignes, règles de sécurité et exigences du référentiel.', defaults={'ordre': 1})
            # savoirs génériques par référentiel
            for code, lib, fam in [('SST', 'Santé, sécurité au travail et prévention des risques', 'Prévention / sécurité'), ('REG', 'Réglementation, normes et règles de l’art', 'Réglementation'), ('DOC', 'Lecture et exploitation de documents techniques', 'Communication technique')]:
                savoir, _ = SavoirAssocie.objects.get_or_create(referentiel=ref, code=code, defaults={'libelle': lib, 'famille': fam, 'niveau_taxonomique': '2'})
                for comp in list(comp_map.values())[:3]:
                    CompetenceSavoir.objects.get_or_create(competence=comp, savoir=savoir, defaults={'niveau_mobilisation': 'application'})
            # liens tâches/compétences simples
            for tache in TacheReferentiel.objects.filter(activite__referentiel=ref)[:5]:
                for comp in list(comp_map.values())[:2]:
                    TacheCompetence.objects.get_or_create(tache=tache, competence=comp, defaults={'niveau_mobilisation': 'mobilisee'})

        # TP de démonstration exploitables immédiatement
        demo_tps = [
            ('TP-MELEC-001', 'Réaliser et contrôler un simple allumage', 'MELEC', 'FORM', 'ECL', 'CABLAGE'),
            ('TP-CIEL-001', 'Configurer une adresse IP et tester une communication', 'CIEL', 'FORM', 'RES', 'GUIDE'),
            ('TP-FED-001', 'Identifier les éléments d’une installation GTB', 'BTS_FED', 'ECQU', 'GTB', 'DOC'),
        ]
        for code, title, fcode, zcode, theme2code, typecode in demo_tps:
            formation = Formation.objects.filter(code=fcode).first()
            zone = ZoneApprentissage.objects.filter(code=zcode).first()
            theme2 = ThemeSecondaire.objects.filter(code=theme2code).first()
            theme1 = theme2.theme_general if theme2 else None
            type_tp = TypeTP.objects.filter(code=typecode).first()
            tp, created = TP.objects.get_or_create(code=code, defaults={'titre': title, 'formation_principale': formation, 'zone_apprentissage': zone, 'theme_general': theme1, 'theme_secondaire': theme2, 'type_tp': type_tp, 'statut': 'publie', 'resume_apprentissages': 'TP de démonstration chargé automatiquement pour tester TP Manager.', 'temps_estime_minutes': 120})
            if formation:
                comps = Competence.objects.filter(bloc__referentiel__formation=formation)[:2]
                for i, comp in enumerate(comps):
                    TPCompetence.objects.get_or_create(tp=tp, competence=comp, type_lien='travaillee' if i == 0 else 'mobilisee')
                tache = TacheReferentiel.objects.filter(activite__referentiel__formation=formation).first()
                if tache:
                    TPTache.objects.get_or_create(tp=tp, tache=tache)
                savoir = SavoirAssocie.objects.filter(referentiel__formation=formation).first()
                if savoir:
                    TPSavoir.objects.get_or_create(tp=tp, savoir=savoir, defaults={'niveau_mobilisation': 'application'})
                crit = CritereEvaluation.objects.filter(competence__bloc__referentiel__formation=formation).first()
                if crit:
                    TPCritere.objects.get_or_create(tp=tp, critere=crit)
