from __future__ import annotations
from decimal import Decimal
import random
from datetime import timedelta
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from tp_manager.models import TpUser, BacDiplome, BacCompetenceCritere, TPV2, BacCompetence, TPV2CritereOfficiel, TPV2CompetenceOfficielle
from evaluation_manager.models import EvalActivity, EvalCriterionResult, EvalBilanIntermediaire, EvalBilanCompetence, EvalLevel


class Command(BaseCommand):
    help = 'Crée une base exemple Evaluation Manager : 1 élève MELEC, 12 évaluations, 6/7 critères par TP, bilan intermédiaire.'

    def handle(self, *args, **options):
        with transaction.atomic():
            if not BacCompetenceCritere.objects.filter(competence__diplome__code='MELEC').exists():
                call_command('seed_tpmanager_v2')
            eleve = self._student()
            prof = self._prof()
            tps = self._tps(prof)
            self._evaluations(eleve, prof, tps)
        self.stdout.write(self.style.SUCCESS('Base exemple Evaluation Manager chargée : élève demo-eval-melec / 12 évaluations / bilan intermédiaire avec entête 1ère puis Tale.'))

    def _student(self):
        obj, _ = TpUser.objects.update_or_create(
            code='EVAL-MELEC-DEMO',
            defaults={
                'username': 'demo-eval-melec',
                'first_name': 'Alex',
                'last_name': 'Démonstration',
                'formation_code': 'MELEC',
                'formation_name': 'Bac Pro MELEC',
                'class_name': 'TMELEC',
                'group_name': 'Groupe démo',
                'role_principal': 'utilisateur',
                'rights': 'UTILISATEUR',
                'active': True,
            },
        )
        if not obj.password_hash:
            obj.set_password('demo1234')
            obj.save(update_fields=['password_hash'])
        return obj

    def _prof(self):
        obj, _ = TpUser.objects.update_or_create(
            code='PROF-0001',
            defaults={
                'username': 'prof-0001',
                'first_name': 'Prof',
                'last_name': 'Démo',
                'formation_code': 'MELEC',
                'formation_name': 'Bac Pro MELEC',
                'class_name': '',
                'role_principal': 'professeur',
                'rights': 'TP_EDIT,TP_ADMIN',
                'active': True,
            },
        )
        if not obj.password_hash:
            obj.set_password('prof1234')
            obj.save(update_fields=['password_hash'])
        return obj

    def _tps(self, prof):
        diplome = BacDiplome.objects.get(code='MELEC')
        rows = [
            ('MELEC-DOM-KNX-001', 'Commande d’éclairage connecté KNX', 'DOM - Domotique', 'KNX - Bus de terrain'),
            ('MELEC-MES-ENE-002', 'Mesures électriques et qualité d’énergie', 'MES - Mesures', 'ENE - Énergie'),
            ('MELEC-GTB-SUP-003', 'Supervision GTB et remontée d’informations', 'GTB - Gestion technique bâtiment', 'SUP - Supervision'),
            ('MELEC-CAB-TAB-004', 'Raccordement d’un tableau divisionnaire', 'CAB - Câblage', 'TAB - Tableau'),
            ('MELEC-SEC-HAB-005', 'Sécurité, habilitation et consignation', 'SEC - Sécurité', 'HAB - Habilitation'),
            ('MELEC-DIA-CAP-006', 'Diagnostic d’un défaut capteur', 'DIA - Diagnostic', 'CAP - Capteur'),
            ('MELEC-REG-PAC-007', 'Paramétrage d’une régulation de PAC', 'REG - Régulation', 'PAC - Pompe à chaleur'),
            ('MELEC-RES-VDI-008', 'Réseau VDI et brassage domestique', 'RES - Réseau', 'VDI - VDI'),
            ('MELEC-IND-MOT-009', 'Départ moteur et protections', 'IND - Industriel', 'MOT - Moteur'),
            ('MELEC-MAI-DEP-010', 'Maintenance corrective d’un circuit de commande', 'MAI - Maintenance', 'DEP - Dépannage'),
            ('MELEC-COM-CLI-011', 'Compte rendu client après intervention', 'COM - Communication', 'CLI - Client'),
            ('MELEC-PRJ-SMB-012', 'Mini-projet Smart Building', 'PRJ - Projet', 'SMB - Smart Building'),
        ]
        tps = []
        for idx, (code, title, theme, sub) in enumerate(rows, start=1):
            tp, _ = TPV2.objects.update_or_create(
                code=code,
                defaults={
                    'titre': title,
                    'diplome': diplome,
                    'niveau_classe': 'Tale MELEC',
                    'domaine_principal': theme,
                    'sous_theme': sub,
                    'usage_pedagogique': 'evaluation' if idx in {2,6,9,12} else 'entrainement',
                    'duree_minutes': 180 if idx % 3 else 240,
                    'resume_eleve': f'Activité démo : {title}',
                    'objectifs_prof': 'Activité créée pour démontrer le tableau de bord Evaluation Manager.',
                    'problematique_metier': 'Réaliser l’activité puis renseigner les critères observables.',
                    'bareme_total': Decimal('20.00') if idx in {2,4,6,9,12} else None,
                    'statut': 'publie',
                    'auteur': prof,
                },
            )
            tps.append(tp)
        return tps

    def _evaluations(self, eleve, prof, tps):
        random.seed(4260)
        criteria = list(BacCompetenceCritere.objects.filter(competence__diplome__code='MELEC').select_related('competence').order_by('competence__code','ordre'))
        # Favorise des paquets cohérents, mais garde une part aléatoire pour démontrer la matrice.
        by_comp = {}
        for c in criteria:
            by_comp.setdefault(c.competence.code, []).append(c)
        comp_windows = [
            ['C01','C02','C10'], ['C05','C06','C07'], ['C04','C05','C10'], ['C02','C04','C11'],
            ['C01','C02','C12'], ['C08','C09','C05'], ['C06','C07','C10'], ['C03','C04','C10'],
            ['C05','C08','C09'], ['C08','C11','C12'], ['C11','C12','C13'], ['C01','C04','C05','C10'],
        ]
        levels = [EvalLevel.NA, EvalLevel.EC, EvalLevel.A, EvalLevel.PA]
        today = timezone.localdate()
        start = today - timedelta(days=90)
        created_activities = []
        for idx, tp in enumerate(tps, start=1):
            classe_eval = '1MELEC' if idx <= 5 else 'TMELEC'
            act, _ = EvalActivity.objects.update_or_create(
                eleve=eleve, tp=tp,
                defaults={
                    'code_eval': f'EV{idx:02d}',
                    'intitule': tp.titre,
                    'date_activite': start + timedelta(days=idx*6),
                    'formation_code': 'MELEC',
                    'classe': classe_eval,
                    'zone_code': tp.domaine_principal.split(' - ')[0] if tp.domaine_principal else '',
                    'systeme_code': 'SYSTEME-DEMO',
                    'statut': 'evalue_prof',
                    'absent': idx == 5,
                    'non_fait': idx == 5,
                    'a_refaire': idx in {5, 10},
                    'remediation_necessaire': idx in {6, 10},
                    'tp_note': bool(tp.bareme_total),
                    'bareme_total': tp.bareme_total,
                    'evaluateur': prof,
                    'date_validation_prof': timezone.now(),
                    'prof_commentaire': 'Évaluation démo générée automatiquement.',
                },
            )
            selected = []
            for comp in comp_windows[idx-1]:
                selected.extend(random.sample(by_comp.get(comp, []), min(2, len(by_comp.get(comp, [])))))
            selected = selected[:random.choice([6,7])] or random.sample(criteria, 6)
            pct = Decimal('100') / Decimal(len(selected))
            for crit in selected:
                prof_level = EvalLevel.AB if act.absent else random.choices(levels, weights=[1,3,4,1], k=1)[0]
                auto_level = random.choices(levels, weights=[1,3,4,1], k=1)[0]
                res, _ = EvalCriterionResult.objects.update_or_create(
                    activity=act, critere=crit,
                    defaults={
                        'auto_niveau': auto_level,
                        'prof_niveau': prof_level,
                        'pourcentage': pct.quantize(Decimal('0.01')),
                        'a_refaire': prof_level in {EvalLevel.NA, EvalLevel.EC} and idx in {6,10,11},
                        'commentaire_prof': 'Résultat généré pour démonstration.',
                    }
                )
                TPV2CritereOfficiel.objects.update_or_create(tp=tp, critere=crit, defaults={'type_lien': 'evaluee', 'pourcentage': pct})
                TPV2CompetenceOfficielle.objects.update_or_create(tp=tp, competence=crit.competence, type_lien='evaluee')
            act.calculate_note(save=True)
            created_activities.append(act)
        self._bilan(eleve, prof, created_activities[:5])

    def _bilan(self, eleve, prof, activities):
        bilan, _ = EvalBilanIntermediaire.objects.update_or_create(
            eleve=eleve, nom='Bilan intermédiaire P1',
            defaults={
                'type_bilan': 'periode',
                'date_bilan': activities[-1].date_activite + timedelta(days=3) if activities else timezone.localdate(),
                'formation_code': 'MELEC',
                'classe': activities[-1].classe if activities else '1MELEC',
                'commentaire': 'Bilan intermédiaire généré depuis les cinq premières évaluations démo.',
                'validateur': prof,
            }
        )
        comp_levels = {}
        priority = {EvalLevel.NA: 1, EvalLevel.EC: 2, EvalLevel.A: 3, EvalLevel.PA: 4, EvalLevel.NE: 0, EvalLevel.AB: 0}
        for act in activities:
            for r in act.criteria_results.select_related('critere__competence'):
                comp = r.critere.competence
                lvl = r.niveau_prof_effectif()
                old = comp_levels.get(comp)
                if old is None or priority.get(lvl,0) < priority.get(old,0):
                    comp_levels[comp] = lvl
        for comp, lvl in comp_levels.items():
            EvalBilanCompetence.objects.update_or_create(
                bilan=bilan, competence=comp,
                defaults={'niveau': lvl, 'date_validation': bilan.date_bilan if lvl in {EvalLevel.A, EvalLevel.PA} else None, 'commentaire': 'Synthèse automatique de démonstration.'}
            )
