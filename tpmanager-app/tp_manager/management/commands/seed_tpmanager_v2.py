from __future__ import annotations
import json
from pathlib import Path
from django.core.management.base import BaseCommand
from django.db import transaction
from tp_manager.models import (
    BacDiplome, BacPole, BacUnite, BacCompetence, BacBloc, BacBlocCompetence,
    BacChampTP, BacChampTPOption, CompetencePivot, TPV2TransferRule,
    BacActivite, BacTache, BacTacheCompetence, BacCompetenceCritere,
    BacAttitudeProfessionnelle, BacCompetenceAttitude, TPV2CriterionLibrary,
)


def _official_comp_code(value):
    raw = str(value or '').strip().upper()
    # C1..C9 => C01..C09 pour éviter les tris C1, C10, C2.
    if raw.startswith('C') and raw[1:].isdigit():
        return f'C{int(raw[1:]):02d}'
    return raw


class Command(BaseCommand):
    help = 'Charge les bases CIEL / MFER / MELEC / BTS FED / BTS Électrotechnique pour TP Manager V2 sans écraser les données existantes.'

    def handle(self, *args, **options):
        fixture_dir = Path(__file__).resolve().parents[2] / 'fixtures'
        with transaction.atomic():
            self._load_fixture(fixture_dir / 'tpmanager_v2_seed_bac_ciel_mfer_melec.json')
            bts_fixture = fixture_dir / 'tpmanager_v2_seed_bts_fed_electrotechnique.json'
            if bts_fixture.exists():
                self._load_fixture(bts_fixture)
            self._seed_melec_mecanique_referentiel()
            self._seed_transfer_rules()
            self._seed_criteria_library()
        self.stdout.write(self.style.SUCCESS('Bases TP Manager V2 CIEL / MFER / MELEC / BTS FED / BTS Électrotechnique chargées sans écrasement.'))

    def _load_fixture(self, fixture: Path):
        data = json.loads(fixture.read_text(encoding='utf-8'))
        maps = {
            'bacdiplome': {}, 'bacpole': {}, 'bacunite': {}, 'baccompetence': {},
            'bacbloc': {}, 'bacchamptp': {}, 'competencepivot': {},
        }
        for item in data:
            if item['model'].endswith('bacdiplome'):
                f = item['fields']; pk = item['pk']
                obj, _ = BacDiplome.objects.update_or_create(code=f['code'], defaults={
                    'intitule': f.get('intitule',''), 'niveau': f.get('niveau','4'),
                    'version_ref': f.get('version_ref',''), 'source_document': f.get('source_document',''),
                    'description': f.get('description',''), 'actif': f.get('actif', True),
                    'locked_official': True,
                })
                maps['bacdiplome'][pk] = obj
        for item in data:
            model = item['model'].split('.')[-1]; f = item['fields']; pk = item['pk']
            if model == 'bacpole':
                diplome = maps['bacdiplome'].get(f['diplome'])
                if diplome:
                    obj, _ = BacPole.objects.update_or_create(diplome=diplome, code=f['code'], defaults={'libelle_officiel': f['libelle_officiel'], 'ordre': f.get('ordre',100), 'locked_official': True})
                    maps['bacpole'][pk]=obj
            elif model == 'bacunite':
                diplome = maps['bacdiplome'].get(f['diplome'])
                if diplome:
                    obj, _ = BacUnite.objects.update_or_create(diplome=diplome, code=f['code'], defaults={'libelle_officiel': f['libelle_officiel'], 'ordre': f.get('ordre',100), 'locked_official': True})
                    maps['bacunite'][pk]=obj
            elif model == 'baccompetence':
                diplome = maps['bacdiplome'].get(f['diplome'])
                if diplome:
                    obj, _ = BacCompetence.objects.update_or_create(diplome=diplome, code=_official_comp_code(f['code']), defaults={'libelle_officiel': f['libelle_officiel'], 'selectable_bac': f.get('selectable_bac', True), 'note': f.get('note',''), 'locked_official': True})
                    maps['baccompetence'][pk]=obj
            elif model == 'competencepivot':
                obj, _ = CompetencePivot.objects.update_or_create(code=f['code'], defaults={'libelle': f.get('libelle',''), 'description': f.get('description','')})
                maps['competencepivot'][pk]=obj
        for item in data:
            model = item['model'].split('.')[-1]; f = item['fields']; pk = item['pk']
            if model == 'bacbloc':
                diplome = maps['bacdiplome'].get(f['diplome'])
                unite = maps['bacunite'].get(f.get('unite')) if f.get('unite') else None
                if diplome:
                    obj, _ = BacBloc.objects.update_or_create(diplome=diplome, code=f['code'], defaults={'unite': unite, 'libelle_officiel': f['libelle_officiel'], 'ordre': f.get('ordre',100), 'locked_official': True})
                    maps['bacbloc'][pk]=obj
            elif model == 'bacchamptp':
                diplome = maps['bacdiplome'].get(f['diplome'])
                if diplome:
                    obj, _ = BacChampTP.objects.update_or_create(diplome=diplome, code=f['code'], defaults={'libelle': f.get('libelle',''), 'type_champ': f.get('type_champ','text'), 'phase': f.get('phase','general'), 'obligatoire': f.get('obligatoire',False), 'aide': f.get('aide',''), 'ordre': f.get('ordre',100), 'actif': f.get('actif', True)})
                    maps['bacchamptp'][pk]=obj
        for item in data:
            model = item['model'].split('.')[-1]; f = item['fields']
            if model == 'bacbloccompetence':
                bloc = maps['bacbloc'].get(f['bloc'])
                comp = maps['baccompetence'].get(f['competence'])
                if bloc and comp:
                    BacBlocCompetence.objects.update_or_create(bloc=bloc, competence=comp, defaults={'ordre': f.get('ordre',100)})
            elif model == 'bacchamptpoption':
                champ = maps['bacchamptp'].get(f['champ'])
                if champ:
                    BacChampTPOption.objects.update_or_create(champ=champ, valeur=f['valeur'], defaults={'libelle': f.get('libelle',''), 'ordre': f.get('ordre',100)})

    def _seed_melec_mecanique_referentiel(self):
        """Charge la mécanique MELEC : activités → tâches → compétences → critères/AP.
        Les libellés officiels restent verrouillés. Les données sont idempotentes.
        """
        diplome = BacDiplome.objects.filter(code='MELEC').first()
        if not diplome:
            return
        official_competences = {
            'C1': 'Analyser les conditions de l’opération et son contexte',
            'C2': 'Organiser l’opération dans son contexte',
            'C3': 'Définir une installation à l’aide de solutions préétablies',
            'C4': 'Réaliser une installation de manière éco-responsable',
            'C5': 'Contrôler les grandeurs caractéristiques de l’installation',
            'C6': 'Régler, paramétrer les matériels de l’installation',
            'C7': 'Valider le fonctionnement de l’installation',
            'C8': 'Diagnostiquer un dysfonctionnement',
            'C9': 'Remplacer un matériel électrique',
            'C10': 'Exploiter les outils numériques dans le contexte professionnel',
            'C11': 'Compléter les documents liés aux opérations',
            'C12': 'Communiquer entre professionnels sur l’opération',
            'C13': 'Communiquer avec le client/usager sur l’opération',
        }
        comps = {}
        for code, label in official_competences.items():
            norm_code = _official_comp_code(code)
            comp, _ = BacCompetence.objects.update_or_create(
                diplome=diplome, code=norm_code,
                defaults={'libelle_officiel': label, 'selectable_bac': True, 'locked_official': True}
            )
            comps[code] = comp
            comps[norm_code] = comp

        activities = [
            ('A1', 'Préparation des opérations de réalisation, de mise en service et de maintenance'),
            ('A2', 'Réalisation'),
            ('A3', 'Mise en service'),
            ('A4', 'Maintenance'),
            ('A5', 'Communication'),
        ]
        acts = {}
        for ordre, (code, label) in enumerate(activities, start=1):
            act, _ = BacActivite.objects.update_or_create(diplome=diplome, code=code, defaults={'libelle_officiel': label, 'ordre': ordre, 'locked_official': True})
            acts[code] = act

        tasks = [
            ('A1','T1-1','Prendre connaissance du dossier relatif aux opérations à réaliser, le constituer pour une opération simple','totale',False,False,False),
            ('A1','T1-2','Rechercher et expliciter les informations relatives aux opérations et aux conditions d’exécution','totale',False,False,False),
            ('A1','T1-3','Vérifier et compléter si besoin la liste des matériels électriques, équipements et outillages nécessaires aux opérations','totale',False,True,True),
            ('A1','T1-4','Répartir les tâches en fonction des habilitations, des certifications des équipiers et du planning des autres intervenants','totale',True,True,True),
            ('A2','T2-1','Organiser le poste de travail','totale',True,True,True),
            ('A2','T2-2','Implanter, poser, installer les matériels électriques','totale',False,True,True),
            ('A2','T2-3','Câbler, raccorder les matériels électriques','totale',False,True,True),
            ('A2','T2-4','Gérer les activités de son équipe','totale',True,True,True),
            ('A2','T2-5','Coordonner son activité par rapport à celles des autres intervenants','totale',True,True,True),
            ('A2','T2-6','Mener son activité de manière éco-responsable','totale',False,True,True),
            ('A3','T3-1','Réaliser les vérifications, les réglages, les paramétrages, les essais nécessaires à la mise en service de l’installation','totale',False,True,True),
            ('A3','T3-2','Participer à la réception technique et aux levées de réserves de l’installation','partielle',False,True,True),
            ('A4','T4-1','Réaliser une opération de maintenance préventive','totale',False,True,True),
            ('A4','T4-2','Réaliser une opération de dépannage','totale',False,True,True),
            ('A5','T5-1','Participer à la mise à jour du dossier technique de l’installation','totale',False,True,True),
            ('A5','T5-2','Échanger sur le déroulement des opérations, expliquer le fonctionnement de l’installation à l’interne et à l’externe','totale',True,False,True),
            ('A5','T5-3','Conseiller le client, lui proposer une prestation complémentaire, une modification ou une amélioration','totale',False,False,True),
        ]
        taches = {}
        for ordre, (act_code, code, label, auto, resp_p, resp_m, resp_r) in enumerate(tasks, start=1):
            t, _ = BacTache.objects.update_or_create(
                activite=acts[act_code], code=code,
                defaults={'libelle_officiel': label, 'autonomie': auto, 'responsabilite_personnes': resp_p, 'responsabilite_moyens': resp_m, 'responsabilite_resultat': resp_r, 'ordre': ordre, 'locked_official': True}
            )
            taches[code] = t

        mapping = {
            'T1-1': {'C1':2,'C3':2,'C10':2,'C11':2,'C12':2},
            'T1-2': {'C1':2,'C10':2,'C12':2},
            'T1-3': {'C2':2,'C10':1,'C11':2,'C12':1},
            'T1-4': {'C1':2,'C2':2,'C10':1,'C12':1},
            'T2-1': {'C2':2,'C10':1},
            'T2-2': {'C2':1,'C4':2,'C5':2,'C10':1,'C11':1},
            'T2-3': {'C2':1,'C4':2,'C5':2,'C10':1,'C11':1},
            'T2-4': {'C2':2,'C10':1,'C12':2},
            'T2-5': {'C2':2,'C10':1,'C12':2},
            'T2-6': {'C2':2,'C4':2,'C10':1},
            'T3-1': {'C2':1,'C5':2,'C6':2,'C7':2,'C8':1,'C9':1,'C10':1},
            'T3-2': {'C2':1,'C5':2,'C6':2,'C7':2,'C8':1,'C9':1,'C10':1},
            'T4-1': {'C2':1,'C5':2,'C7':2,'C9':2,'C10':1},
            'T4-2': {'C2':2,'C5':2,'C6':2,'C7':2,'C8':2,'C9':2,'C10':1},
            'T5-1': {'C10':2,'C11':2,'C12':2,'C13':1},
            'T5-2': {'C10':1,'C12':2,'C13':2},
            'T5-3': {'C1':1,'C10':1,'C11':1,'C12':1,'C13':2},
        }
        for t_code, comp_map in mapping.items():
            for comp_code, poids in comp_map.items():
                BacTacheCompetence.objects.update_or_create(tache=taches[t_code], competence=comps[comp_code], defaults={'poids': poids})

        attitudes_data = {
            'AP1': 'faire preuve de rigueur et de précision',
            'AP2': 'faire preuve d’esprit d’équipe',
            'AP3': 'faire preuve de curiosité et d’écoute',
            'AP4': 'faire preuve d’initiative',
            'AP5': 'faire preuve d’analyse critique',
        }
        attitudes = {}
        for ordre, (code, label) in enumerate(attitudes_data.items(), start=1):
            ap, _ = BacAttitudeProfessionnelle.objects.update_or_create(diplome=diplome, code=code, defaults={'libelle_officiel': label, 'ordre': ordre, 'locked_official': True})
            attitudes[code] = ap

        comp_attitudes = {
            'C1': ['AP1','AP5'], 'C2': ['AP1','AP2','AP4'], 'C3': ['AP1','AP3','AP5'],
            'C4': ['AP1','AP2','AP4'], 'C5': ['AP1','AP5'], 'C6': ['AP1'], 'C7': ['AP1'],
            'C8': ['AP1','AP4','AP5'], 'C9': ['AP1','AP4'], 'C10': ['AP1','AP4','AP5'],
            'C11': ['AP1'], 'C12': ['AP2','AP3','AP5'], 'C13': ['AP3','AP4','AP5'],
        }
        for c_code, ap_codes in comp_attitudes.items():
            for ap_code in ap_codes:
                BacCompetenceAttitude.objects.update_or_create(competence=comps[c_code], attitude=attitudes[ap_code])

        criteria = {
            'C1': ['Les informations nécessaires sont recueillies','Les contraintes techniques et d’exécution sont repérées','Les contraintes liées à l’efficacité énergétique sont repérées','Les risques professionnels sont évalués','Les mesures de prévention de santé et sécurité au travail sont proposées','Les contraintes environnementales sont recensées','Les interactions avec les autres intervenants sont repérées','Les habilitations et certifications nécessaires à l’opération sont identifiées'],
            'C2': ['Après inventaire, les matériels, équipements et outillages manquants sont listés','Le bon d’approvisionnement ou bon de commande est complété','Les tâches sont réparties en fonction des habilitations et certifications des électriciens affectés','La répartition des tâches prend en compte l’avancement des autres intervenants','Les activités sont organisées de manière chronologique','Les contraintes propres au poste de travail y compris environnementales sont prises en compte','Les activités sont réorganisées en fonction des aléas','Les règles de santé et de sécurité au travail sont respectées','Le poste de travail est organisé avec ergonomie','Le poste de travail est approvisionné en matériels, équipements et outillages','Le lieu d’activité est restitué propre et en ordre'],
            'C3': ['Le dossier technique des opérations est constitué et complet','La solution technique proposée répond au besoin du client et elle est pertinente','La solution technique proposée intègre les enjeux d’efficacité énergétique'],
            'C4': ['Les matériels sont posés conformément aux prescriptions et règles de l’art','Le façonnage est réalisé conformément aux prescriptions et règles de l’art','Les câblages et les raccordements sont réalisés conformément aux prescriptions et règles de l’art','Les adaptations techniques nécessaires sont réalisées','Les réalisations respectent les contraintes liées à l’efficacité énergétique','Les autocontrôles sont réalisés et les fiches d’autocontrôles sont complétées','Les déchets sont triés et évacués de manière sélective','Le consommable est utilisé sans gaspillage','Les règles de santé et de sécurité au travail sont respectées','Les procédures de respect de l’environnement des lieux et des biens sont appliquées'],
            'C5': ['Les contrôles visuels et caractéristiques sont réalisés','Les mesures électriques et dimensionnelles sont réalisées','Les mesures liées à l’efficacité énergétique sont réalisées','Les essais adaptés sont réalisés','Les grandeurs contrôlées sont correctement interprétées au regard des prescriptions','Les règles de santé et de sécurité au travail sont respectées'],
            'C6': ['Les réglages sont réalisés conformément aux prescriptions','Les réglages prennent en compte l’efficacité énergétique','Les paramétrages guidés sont réalisés conformément aux prescriptions','Les règles de santé et de sécurité au travail sont respectées'],
            'C7': ['L’installation est mise en fonctionnement conformément aux prescriptions','Le fonctionnement est conforme aux spécifications du cahier des charges, y compris celles liées à l’efficacité énergétique','Les opérations nécessaires à la levée de réserves sont faites','Les règles de santé et de sécurité au travail sont respectées'],
            'C8': ['Les informations relatives au dysfonctionnement sont analysées','Le fonctionnement de l’installation est analysé','Le diagnostic est posé','Le diagnostic est pertinent et complet','Les règles de santé et de sécurité au travail sont respectées'],
            'C9': ['Le matériel électrique à remplacer est identifié','Le matériel électrique à remplacer est correctement déposé','Le matériel électrique de remplacement est correctement choisi','Le matériel électrique de remplacement est correctement installé','Le fonctionnement est vérifié après rétablissement des énergies','Les règles de santé et de sécurité au travail sont respectées'],
            'C10': ['Les applications numériques sont exploitées avec pertinence','La recherche d’information est faite avec pertinence','Les moyens et outils de communication numérique sont exploités avec pertinence','Les moyens et outils de communication sont exploités de manière éthique et responsable','Les logiciels sont simples à utiliser'],
            'C11': ['Les documents à compléter sont identifiés','Les informations nécessaires sont identifiées','Les documents sont complétés ou modifiés correctement'],
            'C12': ['Les informations nécessaires à la communication sont identifiées','Les contraintes techniques sont expliquées','Les choix technologiques sont argumentés','Les choix économiques sont expliqués','Les contraintes liées à la performance énergétique de l’installation sont expliquées','L’état d’avancement de l’opération est justifié','Les difficultés sont remontées à la hiérarchie'],
            'C13': ['Les besoins du client sont collectés','Les contraintes techniques d’utilisation et de performances énergétiques de l’installation sont expliquées','Les usages et le fonctionnement de l’installation sont maîtrisés par le client/usager','Les choix technologiques et économiques sont expliqués','L’état d’avancement de l’opération et ses contraintes sont expliqués','Les prestations complémentaires sont expliquées','La satisfaction client est collectée'],
        }
        for c_code, items in criteria.items():
            comp = comps[c_code]
            for idx, label in enumerate(items, start=1):
                BacCompetenceCritere.objects.update_or_create(
                    competence=comp, code=f'{_official_comp_code(c_code)}-CR{idx:02d}',
                    defaults={'libelle_officiel': label, 'ordre': idx, 'locked_official': True}
                )

    def _seed_criteria_library(self):
        """Préremplit une bibliothèque de critères ajoutables filtrables.
        Cette base ne remplace pas les critères officiels du référentiel : elle sert aux critères de réussite
        et aux critères d’évaluation finale ajoutables par le professeur.
        """
        diplomas = {d.code: d for d in BacDiplome.objects.filter(code__in=['CIEL', 'MELEC', 'MFER', 'BTS_FED', 'BTS_ELEC'])}
        rows = [
            ('MELEC','reussite','Électricien bâtiment','DOMOTIQUE','entrainement','Le câblage respecte le schéma fourni','Conducteurs identifiés, raccordements serrés, repérage cohérent.','Travail conforme sans erreur bloquante','', None),
            ('MELEC','evaluation_finale','Électricien bâtiment','MISE EN SERVICE','evaluation','Mise en service sécurisée de l’installation','Les contrôles préalables sont réalisés avant mise sous tension.','','Installation fonctionnelle et vérifiée selon les consignes.', 4),
            ('CIEL','reussite','Technicien réseau','RÉSEAU','entrainement','L’équipement communique sur le réseau prévu','Adressage, connectivité et service attendu validés.','Communication validée par test.', '', None),
            ('CIEL','evaluation_finale','Technicien réseau','CYBERSÉCURITÉ','evaluation','Configuration réseau documentée et justifiée','Les paramètres essentiels sont renseignés et cohérents.','','Compte rendu technique exploitable, tests inclus.', 4),
            ('MFER','reussite','Frigoriste / énergéticien','PAC','entrainement','Les grandeurs de fonctionnement sont relevées correctement','Températures, pressions ou intensités sont mesurées selon procédure.','Relevés complets et cohérents.', '', None),
            ('MFER','evaluation_finale','Frigoriste / énergéticien','RÉGULATION','evaluation','Diagnostic argumenté sur le fonctionnement énergétique','Les causes probables sont identifiées à partir des mesures.','','Diagnostic cohérent et action corrective proposée.', 5),
            ('BTS_FED','reussite','Technicien supérieur FED','GTB','projet','Les données de supervision sont exploitées','Les tendances ou alarmes sont interprétées dans le contexte du bâtiment.','Analyse exploitable.', '', None),
            ('BTS_FED','evaluation_finale','Technicien supérieur FED','ÉNERGIE','evaluation','La solution proposée est justifiée techniquement','Les choix prennent en compte confort, énergie, contraintes et exploitation.','','Argumentation technique structurée.', 6),
            ('BTS_ELEC','reussite','Technicien supérieur électrotechnique','ÉLECTROTECHNIQUE','projet','La solution technique est cohérente avec le besoin','Les constituants sont choisis et justifiés.','Choix cohérents.', '', None),
            ('BTS_ELEC','evaluation_finale','Technicien supérieur électrotechnique','CHANTIER','evaluation','La conduite de projet est organisée et tracée','Planning, risques, ressources et livrables sont identifiés.','','Organisation réaliste et argumentée.', 6),
            (None,'reussite','Tous métiers','COMMUNICATION TECHNIQUE','entrainement','Le compte rendu est exploitable par un autre professionnel','Informations, mesures et conclusion sont lisibles et structurées.','Compte rendu clair.', '', None),
            (None,'evaluation_finale','Tous métiers','SÉCURITÉ','evaluation','Les règles de sécurité adaptées sont respectées','Les risques sont identifiés et les protections utilisées.','','Aucune mise en danger, consignes respectées.', 4),
        ]
        for code, typ, metier, theme, usage, libelle, desc, niveau, indicateur, bareme in rows:
            diplome = diplomas.get(code) if code else None
            TPV2CriterionLibrary.objects.update_or_create(
                diplome=diplome, type_critere=typ, libelle=libelle,
                defaults={
                    'metier': metier, 'theme': theme, 'usage_recommande': usage, 'description': desc,
                    'niveau_attendu': niveau, 'indicateur': indicateur or desc, 'bareme': bareme,
                    'actif': True, 'ordre': 100,
                }
            )

    def _seed_transfer_rules(self):
        diplomas = {d.code: d for d in BacDiplome.objects.filter(code__in=['CIEL', 'MFER', 'MELEC', 'BTS_FED', 'BTS_ELEC'])}
        for code, libelle, description in [
            ('PIV_SUPERVISER', 'Exploiter une supervision ou des données techniques', 'Pivot interne pour GTB, supervision, données, capteurs, alarmes et suivi énergétique.'),
            ('PIV_CONCEVOIR', 'Concevoir / définir une solution technique', 'Pivot interne pour études, conception, architecture, choix ou définition de solutions.'),
            ('PIV_DIMENSIONNER', 'Dimensionner / choisir des constituants', 'Pivot interne pour calculs, dimensionnement, choix matériel, comparaison technique.'),
            ('PIV_PLANIFIER', 'Planifier / conduire un projet', 'Pivot interne pour organisation, planification, suivi, conduite et animation.'),
            ('PIV_CHIFFRER', 'Chiffrer / établir une offre', 'Pivot interne pour devis, coûts, offre commerciale et bilan économique.'),
            ('PIV_GTBDOMO', 'GTB / domotique / bâtiment communicant', 'Pivot interne pour systèmes bâtiment communicants, supervision, protocoles, pilotage et données.'),
        ]:
            CompetencePivot.objects.get_or_create(code=code, defaults={'libelle': libelle, 'description': description})
        pivots = {p.code: p for p in CompetencePivot.objects.all()}
        rules = [
            # Bac Pro : règles initiales conservées
            ('MELEC','CIEL','PIV_CONFIGURER','T3','Domotique, GTB et systèmes communicants transférables avec recentrage réseau, adressage, supervision et cybersécurité de base.','Ne pas valider les gestes électriques avancés comme compétences CIEL si le TP ne les travaille pas.'),
            ('CIEL','MELEC','PIV_CONFIGURER','T2','Transfert possible en découverte pour équipements connectés, supervision ou domotique.','La conformité d’installation électrique doit être ajoutée côté MELEC si elle est évaluée.'),
            ('MFER','MELEC','PIV_METTRE_SERVICE','T3','PAC, régulation et mise en service transférables vers MELEC sur la partie électrique/commande.','Ne pas transférer les opérations frigorifiques spécifiques.'),
            ('MELEC','MFER','PIV_METTRE_SERVICE','T2','Transfert partiel vers MFER si le TP porte sur pilotage énergétique, régulation ou PAC connectée.','Les critères froid, fluide et performance énergétique doivent être repris côté MFER.'),
            ('CIEL','MFER','PIV_SUPERVISER','T2','Supervision, capteurs et données transférables en découverte vers MFER.','Ne valide pas la compétence frigorifique sans support métier adapté.'),
            ('MFER','CIEL','PIV_SUPERVISER','T2','PAC connectée, données de régulation et capteurs transférables vers CIEL.','Recentrer sur communication, réseau, données et sécurité.'),
            ('CIEL','MELEC','PIV_DIAGNOSTIQUER','T3','Démarche de diagnostic transférable sur systèmes communicants.','Les grandeurs et essais doivent rester ceux du diplôme cible.'),
            ('MELEC','MFER','PIV_DIAGNOSTIQUER','T3','Diagnostic électrique/régulation transférable si associé à une installation thermique.','Pas de substitution aux diagnostics froid métier.'),
            # BTS ajoutés : passerelles montantes et transversales
            ('MELEC','BTS_ELEC','PIV_METTRE_SERVICE','T3','Un TP MELEC peut servir de support BTS Électrotechnique en découverte ou consolidation si l’on ajoute étude, justification, conduite ou diagnostic de niveau 5.','Ne pas présenter une simple exécution Bac Pro comme validation BTS sans exigence d’analyse, dimensionnement ou conduite de projet.'),
            ('BTS_ELEC','MELEC','PIV_METTRE_SERVICE','T3','Un TP BTS Électrotechnique peut être simplifié vers MELEC en recentrant sur préparation, réalisation, contrôle, réglage et mise en service.','Retirer les exigences de dimensionnement, simulation ou conduite d’affaire non attendues au niveau Bac Pro.'),
            ('MFER','BTS_FED','PIV_METTRE_SERVICE','T3','Un TP MFER sur PAC, froid, régulation ou performance peut devenir support BTS FED si l’on ajoute analyse système, performance, mesures et justification.','Ne pas valider la conduite de projet BTS si le TP ne comporte ni dossier, ni chiffrage, ni communication technique.'),
            ('BTS_FED','MFER','PIV_MESURER','T3','Un TP BTS FED peut être adapté vers MFER en conservant le système froid/énergie et en recentrant sur l’intervention, la mise en service ou la maintenance.','Supprimer ou alléger les attendus commerciaux, projet et dimensionnement non ciblés.'),
            ('CIEL','BTS_FED','PIV_GTBDOMO','T2','Les TP CIEL orientés supervision, réseau, capteurs ou données peuvent alimenter l’option DBC du BTS FED en découverte ou transfert partiel.','Ajouter le contexte énergétique/bâtiment et les performances système pour rester dans FED.'),
            ('BTS_FED','CIEL','PIV_GTBDOMO','T2','Les TP FED DBC peuvent être adaptés vers CIEL sur réseaux, données, cybersécurité de base et supervision.','Ne pas valider la performance énergétique FED comme compétence CIEL.'),
            ('MELEC','BTS_FED','PIV_GTBDOMO','T2','Les TP MELEC bâtiment connecté peuvent être transférés vers BTS FED DBC si l’on ajoute analyse système, performance, programmation ou conduite de projet.','Ne pas limiter le TP à du câblage si l’objectif cible est BTS FED.'),
            ('BTS_FED','MELEC','PIV_GTBDOMO','T3','Les TP FED DBC/GTB peuvent être simplifiés vers MELEC en ciblant raccordement, paramétrage, contrôle et communication client/usager.','Les exigences de niveau BTS doivent être explicitement retirées.'),
            ('BTS_ELEC','BTS_FED','PIV_CONCEVOIR','T3','Passerelle pertinente sur études de bâtiment, énergie, GTB, dimensionnement, choix de solutions, planning et dossier technique.','Recentrer les grandeurs métier : électrique pour BTS Électrotechnique, fluide/énergie/domotique pour BTS FED.'),
            ('BTS_FED','BTS_ELEC','PIV_CONCEVOIR','T3','Passerelle pertinente sur avant-projet, documents techniques, conduite, chiffrage et systèmes énergétiques communicants.','Ne pas transférer sans adaptation les compétences spécifiques froid/fluide vers l’électrotechnique.'),
            ('BTS_ELEC','CIEL','PIV_SUPERVISER','T2','Transfert possible en découverte pour supervision, réseaux techniques, équipements communicants et données de fonctionnement.','Le TP cible CIEL doit ajouter l’angle réseau, donnée ou cybersécurité.'),
            ('CIEL','BTS_ELEC','PIV_SUPERVISER','T2','Un TP CIEL peut servir de support BTS Électrotechnique s’il est replacé dans un ouvrage électrique, une installation ou un équipement électrique.','Ajouter normes, dossier technique, mesures ou mise en service électrique selon l’unité ciblée.'),
        ]
        for src, dst, piv, lvl, reco, lim in rules:
            if src in diplomas and dst in diplomas:
                TPV2TransferRule.objects.update_or_create(
                    source=diplomas[src],
                    cible=diplomas[dst],
                    competence_pivot=pivots.get(piv),
                    defaults={'niveau': lvl, 'recommandation': reco, 'limites': lim}
                )
