from __future__ import annotations
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db.models import Count, Q
from django.http import JsonResponse
from django.conf import settings
from decimal import Decimal, InvalidOperation
import os
import sqlite3
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from .context_processors import current_tp_user
from .permissions import tp_login_required, tp_prof_required
from .models import (
    BacDiplome, BacChampTP, BacChampTPOption, TPV2, TPV2ChampValeur,
    BacActivite, BacTache, BacTacheCompetence, BacCompetenceCritere, BacAttitudeProfessionnelle,
    TPV2ActiviteOfficielle, TPV2TacheOfficielle, TPV2CompetenceOfficielle,
    TPV2CritereOfficiel, TPV2AttitudeOfficielle, TPV2CritereReussite, TPV2CritereEvaluationFinale,
    TPV2Document, TPV2ResourceGroup, TPV2ResourceItem, TPV2TransferRule,
    TPV2LinkedBlock, TPV2LinkedTPItem, TPV2CriterionLibrary, SystemePedagogiqueRef,
    ParcoursEleveTP, TpUser, SequencePedagogique,
)
from .forms_v2 import (
    TPV2Form, TPV2FilterForm, TPV2OfficialCompetenceForm, TPV2SuccessCriterionForm,
    TPV2FinalEvaluationCriterionForm, TPV2DocumentForm, TPV2ResourceGroupForm,
    TPV2ResourceItemForm, TPV2LinkedBlockForm, TPV2LinkedTPItemForm, TPV2ParcoursAssignForm,
    build_dynamic_field_definitions, save_dynamic_values,
)



def _ids_from_post(post_data, key):
    values = post_data.getlist(key) if hasattr(post_data, 'getlist') else []
    ids = set()
    for value in values:
        try:
            ids.add(int(value))
        except (TypeError, ValueError):
            continue
    return ids


def _selected_referentiel_ids(tp=None, post_data=None):
    if post_data is not None:
        return {
            'activities': _ids_from_post(post_data, 'ref_activities'),
            'tasks': _ids_from_post(post_data, 'ref_tasks'),
            'competences': _ids_from_post(post_data, 'ref_competences'),
            'criteria': _ids_from_post(post_data, 'ref_criteria'),
            'attitudes': _ids_from_post(post_data, 'ref_attitudes'),
            'competence_links': {},
            'criterion_links': {},
        }
    if not tp:
        return {'activities': set(), 'tasks': set(), 'competences': set(), 'criteria': set(), 'attitudes': set(), 'competence_links': {}, 'criterion_links': {}}
    competence_links = {x.competence_id: x for x in tp.competences_officielles.all()}
    criterion_links = {x.critere_id: x for x in tp.criteres_officiels_selectionnes.all()}
    return {
        'activities': set(tp.activites_officielles.values_list('activite_id', flat=True)),
        'tasks': set(tp.taches_officielles.values_list('tache_id', flat=True)),
        'competences': set(competence_links.keys()),
        'criteria': set(criterion_links.keys()),
        'attitudes': set(tp.attitudes_officielles_selectionnees.values_list('attitude_id', flat=True)),
        'competence_links': competence_links,
        'criterion_links': criterion_links,
    }


def build_referentiel_context(diplome, tp=None, post_data=None):
    if not diplome:
        return None
    selected = _selected_referentiel_ids(tp=tp, post_data=post_data)
    activities = []
    task_competence_map = {}
    competence_task_map = {}
    for activite in BacActivite.objects.filter(diplome=diplome).prefetch_related('taches__competences_liees__competence').order_by('ordre', 'code'):
        task_rows = []
        for tache in activite.taches.all().order_by('ordre', 'code'):
            links = list(tache.competences_liees.select_related('competence').order_by('competence__code'))
            comp_ids = [link.competence_id for link in links]
            task_competence_map[tache.id] = comp_ids
            for cid in comp_ids:
                competence_task_map.setdefault(cid, set()).add(tache.id)
            task_rows.append({'obj': tache, 'selected': tache.id in selected['tasks'], 'links': links, 'competence_ids': ','.join(str(i) for i in comp_ids)})
        activities.append({'obj': activite, 'selected': activite.id in selected['activities'], 'tasks': task_rows})
    competences = []
    for comp in diplome.competences_officielles.filter(selectable_bac=True).prefetch_related('criteres_officiels', 'attitudes_liees__attitude').order_by('code'):
        task_ids = sorted(competence_task_map.get(comp.id, []))
        attitude_ids = [a.attitude_id for a in comp.attitudes_liees.all()]
        comp_link = selected.get('competence_links', {}).get(comp.id)
        criteria_rows = []
        for crit in comp.criteres_officiels.all().order_by('ordre', 'code'):
            crit_link = selected.get('criterion_links', {}).get(crit.id)
            criteria_rows.append({
                'obj': crit,
                'selected': crit.id in selected['criteria'],
                'type_lien': crit_link.type_lien if crit_link else 'travaillee',
                'bareme': crit_link.bareme if crit_link else '',
            })
        competences.append({
            'obj': comp,
            'selected': comp.id in selected['competences'],
            'type_lien': comp_link.type_lien if comp_link else 'travaillee',
            'niveau_evaluation': comp_link.niveau_evaluation if comp_link else '',
            'bareme': comp_link.bareme if comp_link else '',
            'task_ids': ','.join(str(i) for i in task_ids),
            'criteria': criteria_rows,
            'attitude_ids': ','.join(str(i) for i in attitude_ids),
        })
    attitudes = []
    for attitude in diplome.attitudes_professionnelles.all().order_by('ordre', 'code'):
        comp_ids = list(attitude.competences_liees.values_list('competence_id', flat=True))
        attitudes.append({'obj': attitude, 'selected': attitude.id in selected['attitudes'], 'competence_ids': ','.join(str(i) for i in comp_ids)})
    return {'activities': activities, 'competences': competences, 'attitudes': attitudes, 'selected': selected}



def _safe_decimal(value):
    value = (value or '').strip() if isinstance(value, str) else value
    if value in ('', None):
        return None
    try:
        return Decimal(str(value).replace(',', '.'))
    except (InvalidOperation, ValueError, TypeError):
        return None


def _safe_type_lien(value):
    allowed = {'mobilisee', 'travaillee', 'evaluee', 'certification'}
    return value if value in allowed else 'travaillee'

def _safe_percent(value):
    value = _safe_decimal(value)
    if value is None:
        return None
    if value < 0:
        return Decimal('0')
    if value > 100:
        return Decimal('100')
    return value


def _points_from_percent(total, percent):
    if total is None or percent is None:
        return None
    try:
        return (Decimal(total) * Decimal(percent) / Decimal('100')).quantize(Decimal('0.01'))
    except (InvalidOperation, ValueError, TypeError):
        return None


def save_referentiel_selection(tp, post_data):
    activity_ids = _ids_from_post(post_data, 'ref_activities')
    task_ids = _ids_from_post(post_data, 'ref_tasks')
    competence_ids = _ids_from_post(post_data, 'ref_competences')
    criteria_ids = _ids_from_post(post_data, 'ref_criteria')
    attitude_ids = _ids_from_post(post_data, 'ref_attitudes')
    # Sécurisation côté serveur : on filtre par diplôme et par dépendances officielles.
    allowed_activities = set(BacActivite.objects.filter(diplome=tp.diplome, id__in=activity_ids).values_list('id', flat=True))
    allowed_tasks = set(BacTache.objects.filter(activite__diplome=tp.diplome, activite_id__in=allowed_activities, id__in=task_ids).values_list('id', flat=True))
    allowed_competences = set(BacTacheCompetence.objects.filter(tache_id__in=allowed_tasks, competence_id__in=competence_ids, competence__diplome=tp.diplome).values_list('competence_id', flat=True).distinct())
    allowed_criteria = set(BacCompetenceCritere.objects.filter(competence_id__in=allowed_competences, id__in=criteria_ids).values_list('id', flat=True))
    allowed_attitudes = set(BacAttitudeProfessionnelle.objects.filter(diplome=tp.diplome, competences_liees__competence_id__in=allowed_competences, id__in=attitude_ids).values_list('id', flat=True).distinct())

    TPV2ActiviteOfficielle.objects.filter(tp=tp).exclude(activite_id__in=allowed_activities).delete()
    for aid in allowed_activities:
        TPV2ActiviteOfficielle.objects.get_or_create(tp=tp, activite_id=aid)
    TPV2TacheOfficielle.objects.filter(tp=tp).exclude(tache_id__in=allowed_tasks).delete()
    for tid in allowed_tasks:
        TPV2TacheOfficielle.objects.get_or_create(tp=tp, tache_id=tid)
    TPV2CompetenceOfficielle.objects.filter(tp=tp).exclude(competence_id__in=allowed_competences).delete()
    for cid in allowed_competences:
        qs = TPV2CompetenceOfficielle.objects.filter(tp=tp, competence_id=cid)
        obj = qs.first()
        qs.exclude(pk=obj.pk if obj else None).delete()
        if obj is None:
            obj = TPV2CompetenceOfficielle(tp=tp, competence_id=cid, type_lien='mobilisee')
            obj.save()
    TPV2CritereOfficiel.objects.filter(tp=tp).exclude(critere_id__in=allowed_criteria).delete()
    for crit_id in allowed_criteria:
        TPV2CritereOfficiel.objects.get_or_create(tp=tp, critere_id=crit_id, defaults={'type_lien': 'mobilisee'})
    TPV2AttitudeOfficielle.objects.filter(tp=tp).exclude(attitude_id__in=allowed_attitudes).delete()
    for att_id in allowed_attitudes:
        TPV2AttitudeOfficielle.objects.get_or_create(tp=tp, attitude_id=att_id)

def _is_prof(user):
    return bool(user and user.is_prof_like)


def _can_edit_v2(user, tp):
    if not user:
        return False
    if user.is_prof_like:
        return True
    return bool(tp.auteur_id == user.id and tp.statut in {'brouillon', 'relecture'})



def _formation_alias_for_code(code):
    aliases = {
        'CIEL': 'CIEL',
        'MELEC': 'MELEC',
        'MFER': 'MFER',
        'BTS_FED': 'FED',
        'BTS_ELEC': 'STEL',
    }
    if not code:
        return ''
    return aliases.get(code, code.replace('BAC_PRO_', '').replace('BACPRO_', '').replace('BTS_', '').replace('CAP_', 'CAP'))


def _level_options_for_diplome(diplome=None):
    """Options de niveau filtrées par type de formation.

    Bac Pro : 2nde / 1ère / Tale. BTS et CAP : 1ère année / 2ème année.
    Les bases CAP seront ajoutées plus tard, mais le comportement est déjà prévu.
    """
    if not diplome:
        return [
            '2nde CIEL', '1ère CIEL', 'Tale CIEL',
            '2nde MELEC', '1ère MELEC', 'Tale MELEC',
            '2nde MFER', '1ère MFER', 'Tale MFER',
            '1ère année FED', '2ème année FED',
            '1ère année STEL', '2ème année STEL',
            '1ère année CAP', '2ème année CAP',
        ]
    code = diplome.code or ''
    alias = _formation_alias_for_code(code)
    if code.startswith('BTS_') or alias in {'FED', 'STEL'}:
        return [f'1ère année {alias}', f'2ème année {alias}']
    if code.startswith('CAP') or alias == 'CAP':
        return [f'1ère année {alias}', f'2ème année {alias}']
    return [f'2nde {alias}', f'1ère {alias}', f'Tale {alias}']


def _tpv2_form_option_lists(selected_diplome=None):
    """Listes indicatives pour datalist HTML : elles n'interdisent pas la saisie manuelle."""
    base_types = ['TP', 'TD', 'PROJET', 'EVAL', 'RECH', 'SAE']
    base_themes = [
        'DOM - Domotique', 'GTB - Gestion technique bâtiment', 'PAC - Pompe à chaleur', 'FRO - Froid',
        'RES - Réseau', 'CYB - Cybersécurité', 'ELE - Électrotechnique', 'CAB - Câblage',
        'MAI - Maintenance', 'DIA - Diagnostic', 'MES - Mise en service', 'SUP - Supervision',
        'ENE - Énergie', 'REG - Régulation', 'MSR - Mesures', 'COM - Communication technique',
    ]
    base_sous_themes = [
        'KNX - KNX', 'JEE - Jeedom', 'WIF - Wi-Fi', 'VLA - VLAN', 'IPA - Adressage IP',
        'MOD - Modbus', 'BAC - Bacnet', 'CAP - Capteurs', 'ACT - Actionneurs',
        'PEA - PAC air/eau', 'PAA - PAC air/air', 'GRF - Groupe froid', 'VAR - Variateur',
        'ECL - Éclairage connecté', 'TAB - Tableau électrique', 'PUI - Mesure de puissance',
        'SEG - Supervision énergétique',
    ]
    base_classes = _level_options_for_diplome(selected_diplome)
    # Enrichissement par les valeurs déjà saisies : la base devient progressivement plus utile.
    qs = TPV2.objects.all()
    if selected_diplome:
        qs = qs.filter(diplome=selected_diplome)
    def values(field, base):
        existing = [v for v in qs.exclude(**{field: ''}).values_list(field, flat=True).distinct()[:150] if v]
        ordered = []
        for item in list(base) + existing:
            if item and item not in ordered:
                ordered.append(item)
        return ordered
    return {
        'types': values('type_activite', base_types),
        'themes': values('domaine_principal', base_themes),
        'sous_themes': values('sous_theme', base_sous_themes),
        'classes': values('niveau_classe', base_classes),
    }

def _tpv2_qs_for_user(user):
    qs = TPV2.objects.select_related('diplome', 'auteur', 'competence_pivot').prefetch_related('competences_officielles__competence')
    if not _is_prof(user):
        qs = qs.filter(statut='publie')
    return qs


def _filter_tpv2(request):
    form = TPV2FilterForm(request.GET or None)
    qs = _tpv2_qs_for_user(current_tp_user(request))
    if form.is_valid():
        q = (form.cleaned_data.get('q') or '').strip()
        if q:
            qs = qs.filter(Q(code__icontains=q) | Q(titre__icontains=q) | Q(resume_eleve__icontains=q) | Q(objectifs_prof__icontains=q) | Q(mots_cles__icontains=q))
        if form.cleaned_data.get('diplome'):
            qs = qs.filter(diplome=form.cleaned_data['diplome'])
        if form.cleaned_data.get('usage'):
            qs = qs.filter(usage_pedagogique=form.cleaned_data['usage'])
        if form.cleaned_data.get('pivot'):
            qs = qs.filter(competence_pivot=form.cleaned_data['pivot'])
        if form.cleaned_data.get('temps_max'):
            qs = qs.filter(duree_minutes__lte=int(float(form.cleaned_data['temps_max']) * 60))
    return form, qs


def dashboard(request):
    user = current_tp_user(request)
    diplome_counts = BacDiplome.objects.filter(actif=True).annotate(tp_count=Count('tps_v2')).order_by('code')
    recent_tps = _tpv2_qs_for_user(user).order_by('-updated_at')[:8]
    stats = {
        'tps': TPV2.objects.count(),
        'publies': TPV2.objects.filter(statut='publie').count(),
        'diplomes': BacDiplome.objects.filter(actif=True).count(),
        'parcours': ParcoursEleveTP.objects.count(),
    }
    return render(request, 'tp_manager/tpv2_dashboard.html', {'stats': stats, 'diplome_counts': diplome_counts, 'recent_tps': recent_tps})


def tp_list(request):
    form, tps = _filter_tpv2(request)
    return render(request, 'tp_manager/tpv2_list.html', {'form': form, 'tps': tps[:800]})


@tp_login_required
def tp_create(request):
    user = current_tp_user(request)
    if not _is_prof(user):
        messages.error(request, 'Création de TP réservée aux professeurs / administrateurs.')
        return redirect('tp_dashboard')
    selected_diplome_id = request.POST.get('diplome') or request.GET.get('diplome')
    selected_diplome = BacDiplome.objects.filter(pk=selected_diplome_id, actif=True).first() if selected_diplome_id else None
    initial = {'diplome': selected_diplome} if selected_diplome else None
    form = TPV2Form(request.POST or None, initial=initial, allow_status=True)
    dynamic_fields = build_dynamic_field_definitions(selected_diplome)
    referentiel_context = build_referentiel_context(selected_diplome, post_data=request.POST if request.method == 'POST' else None)
    existing_values = {}
    for champ in dynamic_fields:
        champ.current_value = ''
    if request.method == 'POST' and form.is_valid():
        if not selected_diplome:
            messages.error(request, 'Choisir un diplôme avant de créer un TP.')
            return redirect('tp_create')
        tp = form.save(commit=False)
        tp.diplome = selected_diplome
        tp.auteur = user
        tp.save()
        save_dynamic_values(tp, request.POST)
        save_referentiel_selection(tp, request.POST)
        messages.success(request, f'TP V2 créé : {tp.code}. Les compétences officielles et ressources peuvent maintenant être associées.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/tpv2_form.html', {
        'form': form,
        'title': 'Créer un TP — TP Manager V2',
        'selected_diplome': selected_diplome,
        'dynamic_fields': dynamic_fields,
        'referentiel_context': referentiel_context,
        'existing_values': existing_values,
        'diplomes': BacDiplome.objects.filter(actif=True).order_by('code'),
        'form_options': _tpv2_form_option_lists(selected_diplome),
    })


def tp_detail(request, pk):
    tp = get_object_or_404(TPV2.objects.select_related('diplome', 'auteur', 'competence_pivot'), pk=pk)
    user = current_tp_user(request)
    if tp.statut != 'publie' and not _can_edit_v2(user, tp):
        messages.error(request, 'TP non publié.')
        return redirect('tp_list')
    referentiel_context = build_referentiel_context(tp.diplome, tp=tp)
    total_comp_points = sum([(c.bareme or Decimal('0')) for c in tp.competences_officielles.all()])
    total_crit_points = sum([(c.bareme or Decimal('0')) for c in tp.criteres_officiels_selectionnes.all()])
    return render(request, 'tp_manager/tpv2_detail.html', {
        'tp': tp,
        'can_edit': _can_edit_v2(user, tp),
        'referentiel_context': referentiel_context,
        'total_comp_points': total_comp_points,
        'total_crit_points': total_crit_points,
    })


@tp_login_required
def tp_update(request, pk):
    tp = get_object_or_404(TPV2, pk=pk)
    user = current_tp_user(request)
    if not _can_edit_v2(user, tp):
        messages.error(request, 'Modification non autorisée pour ce TP.')
        return redirect('tp_detail', tp.pk)
    selected_diplome = tp.diplome
    form = TPV2Form(request.POST or None, instance=tp, allow_status=user.is_prof_like)
    dynamic_fields = build_dynamic_field_definitions(selected_diplome)
    referentiel_context = build_referentiel_context(selected_diplome, tp=tp, post_data=request.POST if request.method == 'POST' else None)
    existing_values = {v.champ_id: v.valeur for v in TPV2ChampValeur.objects.filter(tp=tp)}
    for champ in dynamic_fields:
        champ.current_value = existing_values.get(champ.id, '')
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        if not user.is_prof_like:
            obj.statut = 'relecture'
        obj.save()
        save_dynamic_values(obj, request.POST)
        save_referentiel_selection(obj, request.POST)
        messages.success(request, 'TP V2 modifié.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/tpv2_form.html', {
        'form': form,
        'title': f'Modifier {tp.code}',
        'selected_diplome': selected_diplome,
        'dynamic_fields': dynamic_fields,
        'referentiel_context': referentiel_context,
        'existing_values': existing_values,
        'diplomes': BacDiplome.objects.filter(actif=True).order_by('code'),
        'tp': tp,
        'form_options': _tpv2_form_option_lists(selected_diplome),
    })


@tp_prof_required
def tp_duplicate(request, pk):
    source = get_object_or_404(TPV2, pk=pk)
    if request.method == 'POST':
        user = current_tp_user(request)
        copy = TPV2.objects.create(
            titre=f'{source.titre} — copie',
            type_activite=source.type_activite,
            diplome=source.diplome,
            niveau_classe=source.niveau_classe,
            domaine_principal=source.domaine_principal,
            sous_theme=source.sous_theme,
            usage_pedagogique=source.usage_pedagogique,
            duree_minutes=source.duree_minutes,
            resume_eleve=source.resume_eleve,
            objectifs_prof=source.objectifs_prof,
            problematique_metier=source.problematique_metier,
            mots_cles=source.mots_cles,
            bareme_total=source.bareme_total,
            competence_pivot=source.competence_pivot,
            statut='brouillon',
            version='V1-copie',
            auteur=user,
            source_tp=source,
            commentaire_interne=f'Copie modifiable issue de {source.code}.',
        )
        for val in source.valeurs_champs.select_related('champ'):
            TPV2ChampValeur.objects.create(tp=copy, champ=val.champ, valeur=val.valeur)
        for a in source.activites_officielles.all():
            TPV2ActiviteOfficielle.objects.create(tp=copy, activite=a.activite)
        for t in source.taches_officielles.all():
            TPV2TacheOfficielle.objects.create(tp=copy, tache=t.tache)
        for c in source.competences_officielles.all():
            TPV2CompetenceOfficielle.objects.create(tp=copy, competence=c.competence, type_lien=c.type_lien, niveau_evaluation=c.niveau_evaluation, bareme=c.bareme, pourcentage=c.pourcentage, commentaire=c.commentaire)
        for crit in source.criteres_officiels_selectionnes.all():
            TPV2CritereOfficiel.objects.create(tp=copy, critere=crit.critere, type_lien=crit.type_lien, bareme=crit.bareme, pourcentage=crit.pourcentage)
        for ap in source.attitudes_officielles_selectionnees.all():
            TPV2AttitudeOfficielle.objects.create(tp=copy, attitude=ap.attitude)
        for c in source.criteres_reussite.all():
            TPV2CritereReussite.objects.create(tp=copy, libelle=c.libelle, description=c.description, niveau_attendu=c.niveau_attendu, obligatoire=c.obligatoire, ordre=c.ordre)
        for c in source.criteres_evaluation_finale.all():
            TPV2CritereEvaluationFinale.objects.create(tp=copy, libelle=c.libelle, indicateur=c.indicateur, bareme=c.bareme, commentaire=c.commentaire, ordre=c.ordre)
        for group in source.resource_groups.all():
            new_group = TPV2ResourceGroup.objects.create(tp=copy, titre=group.titre, operator=group.operator, obligatoire=group.obligatoire, ordre=group.ordre, commentaire=group.commentaire)
            for item in group.items.all():
                TPV2ResourceItem.objects.create(group=new_group, source_module=item.source_module, resource_type=item.resource_type, external_id=item.external_id, external_code=item.external_code, libelle=item.libelle, quantite=item.quantite, unite=item.unite, commentaire=item.commentaire)
        messages.success(request, f'Copie créée : {copy.code}. Tu peux maintenant la modifier sans toucher au TP source.')
        return redirect('tp_detail', copy.pk)
    return render(request, 'tp_manager/tpv2_duplicate.html', {'tp': source})


@tp_prof_required
def tp_referentiel_affect(request, pk):
    """Page post-création : qualifier les compétences/critères officiels.

    Les liens référentiel sont sélectionnés dans la création/modification du TP.
    Cette page règle le statut pédagogique global des compétences.
    Le barème et les pourcentages sont portés uniquement par les sous-compétences / critères officiels.
    """
    tp = get_object_or_404(
        TPV2.objects.select_related('diplome', 'auteur')
        .prefetch_related('competences_officielles__competence', 'criteres_officiels_selectionnes__critere__competence'),
        pk=pk,
    )
    if request.method == 'POST':
        tp.bareme_total = _safe_decimal(request.POST.get('bareme_total'))
        tp.mots_cles = (request.POST.get('mots_cles') or '').strip()
        tp.save(update_fields=['bareme_total', 'mots_cles', 'updated_at'])

        for item in tp.competences_officielles.all():
            item.type_lien = _safe_type_lien(request.POST.get(f'comp_type_{item.id}'))
            item.niveau_evaluation = (request.POST.get(f'comp_niveau_{item.id}') or '').strip()[:80]
            item.pourcentage = None
            item.bareme = None
            item.commentaire = (request.POST.get(f'comp_commentaire_{item.id}') or '').strip()
            item.save(update_fields=['type_lien', 'niveau_evaluation', 'pourcentage', 'bareme', 'commentaire', 'updated_at'])

        for item in tp.criteres_officiels_selectionnes.all():
            item.type_lien = _safe_type_lien(request.POST.get(f'crit_type_{item.id}'))
            item.pourcentage = _safe_percent(request.POST.get(f'crit_pourcentage_{item.id}'))
            item.bareme = _points_from_percent(tp.bareme_total, item.pourcentage)
            item.save(update_fields=['type_lien', 'pourcentage', 'bareme', 'updated_at'])

        messages.success(request, 'Affectations référentiel et barèmes enregistrés.')
        return redirect('tp_detail', tp.pk)

    return render(request, 'tp_manager/tpv2_affect_referentiel.html', {'tp': tp})


@tp_prof_required
def parcours_assign(request):
    """Affectation en masse des TP V2 à des élèves.

    Correctif défensif : tant que le modèle historique ParcoursEleveTP pointe encore
    vers l'ancien modèle TP, on affiche la page et on évite de casser le service.
    L'enregistrement complet des parcours TPV2 nécessite une migration dédiée qui
    sera intégrée dans l'évolution suivante.
    """
    form = TPV2ParcoursAssignForm(request.POST or None, filters=request.GET)
    if request.method == 'POST':
        if form.is_valid():
            # Le modèle ParcoursEleveTP historique référence encore TP, pas TPV2.
            # On ne force donc pas une écriture incohérente en base.
            messages.warning(request, 'La sélection est valide, mais l’écriture des parcours TP V2 nécessite la migration parcours dédiée. Aucune donnée n’a été modifiée.')
            return redirect('tpv2_parcours_assign')
        messages.error(request, 'Affectation non enregistrée : vérifier la sélection des TP et des élèves.')
    return render(request, 'tp_manager/tpv2_parcours_assign.html', {
        'form': form,
        'diplomes': BacDiplome.objects.filter(actif=True).order_by('code'),
        'filters': request.GET,
    })


@tp_prof_required
def tp_competence_add(request, tp_pk):
    tp = get_object_or_404(TPV2, pk=tp_pk)
    form = TPV2OfficialCompetenceForm(request.POST or None, tp=tp)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.tp = tp
        item.full_clean()
        item.save()
        messages.success(request, 'Compétence officielle associée au TP.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/form.html', {'form': form, 'title': f'Associer une compétence officielle — {tp.code}'})


@tp_prof_required
def tp_success_criterion_add(request, tp_pk):
    tp = get_object_or_404(TPV2, pk=tp_pk)
    form = TPV2SuccessCriterionForm(request.POST or None, tp=tp)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        lib = form.cleaned_data.get('library_criterion')
        if lib and not item.libelle:
            item.libelle = lib.libelle
        if lib and not item.description:
            item.description = lib.description
        if lib and not item.niveau_attendu:
            item.niveau_attendu = lib.niveau_attendu
        item.tp = tp
        item.save()
        messages.success(request, 'Critère de réussite ajouté.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/form.html', {'form': form, 'title': f'Ajouter un critère de réussite — {tp.code}'})


@tp_prof_required
def tp_final_criterion_add(request, tp_pk):
    tp = get_object_or_404(TPV2, pk=tp_pk)
    form = TPV2FinalEvaluationCriterionForm(request.POST or None, tp=tp)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        lib = form.cleaned_data.get('library_criterion')
        if lib and not item.libelle:
            item.libelle = lib.libelle
        if lib and not item.indicateur:
            item.indicateur = lib.indicateur or lib.description
        if lib and item.bareme is None:
            item.bareme = lib.bareme
        item.tp = tp
        item.save()
        messages.success(request, 'Critère d’évaluation finale ajouté.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/form.html', {'form': form, 'title': f'Ajouter un critère d’évaluation finale — {tp.code}'})


@tp_prof_required
def document_add(request, tp_pk):
    tp = get_object_or_404(TPV2, pk=tp_pk)
    form = TPV2DocumentForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.tp = tp
        doc.uploaded_by = current_tp_user(request)
        doc.save()
        messages.success(request, 'Document ajouté.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/form.html', {'form': form, 'title': f'Ajouter un document — {tp.code}'})


@tp_prof_required
def resource_group_add(request, tp_pk):
    tp = get_object_or_404(TPV2, pk=tp_pk)
    form = TPV2ResourceGroupForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        group = form.save(commit=False)
        group.tp = tp
        group.save()
        messages.success(request, 'Groupe de ressources ajouté.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/form.html', {'form': form, 'title': f'Ajouter un bloc OU de ressources — {tp.code}'})


@tp_prof_required
def resource_item_add(request, group_pk):
    group = get_object_or_404(TPV2ResourceGroup.objects.select_related('tp'), pk=group_pk)
    form = TPV2ResourceItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.group = group
        item.save()
        messages.success(request, 'Ressource ajoutée au groupe.')
        return redirect('tp_detail', group.tp.pk)
    return render(request, 'tp_manager/tpv2_resource_item_form.html', {'form': form, 'group': group, 'title': f'Ajouter une ressource — {group.tp.code}'})



@tp_prof_required
def linked_block_add(request, tp_pk):
    tp = get_object_or_404(TPV2, pk=tp_pk)
    form = TPV2LinkedBlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        block = form.save(commit=False)
        block.tp = tp
        block.save()
        messages.success(request, 'Bloc de TP liés ajouté.')
        return redirect('tp_detail', tp.pk)
    return render(request, 'tp_manager/form.html', {'form': form, 'title': f'Ajouter un bloc de TP liés — {tp.code}'})


@tp_prof_required
def linked_item_add(request, block_pk):
    block = get_object_or_404(TPV2LinkedBlock.objects.select_related('tp'), pk=block_pk)
    form = TPV2LinkedTPItemForm(request.POST or None, block=block, filters=request.GET)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.block = block
        item.full_clean()
        item.save()
        messages.success(request, 'TP lié ajouté au bloc.')
        return redirect('tp_detail', block.tp.pk)
    return render(request, 'tp_manager/tpv2_linked_item_form.html', {'form': form, 'block': block, 'diplomes': BacDiplome.objects.filter(actif=True).order_by('code'), 'usages': TPV2.USAGE_CHOICES, 'filters': request.GET, 'title': f'Ajouter un TP lié — {block.tp.code}'})


def _sqlite_rows(db_path, sql, params=()):
    if not db_path or not os.path.exists(db_path):
        return []
    try:
        con = sqlite3.connect(db_path)
        con.row_factory = sqlite3.Row
        cur = con.execute(sql, params)
        rows = [dict(r) for r in cur.fetchall()]
        con.close()
        return rows
    except Exception:
        return []


def _resource_search_toolmag(q, resource_type='', status=''):
    db = os.environ.get('TPMANAGER_TOOLMAG_DB', '/data/toolmag/toolmag.sqlite3')
    like = f'%{q or ""}%'
    clauses = ['(code LIKE ? OR name LIKE ? OR description LIKE ? OR brand LIKE ? OR model LIKE ?)']
    params = [like, like, like, like, like]
    if resource_type in {'outil', 'mesure'}:
        clauses.append("equipment_type != 'consumable'")
    elif resource_type == 'consommable':
        clauses.append("equipment_type = 'consumable'")
    if status:
        clauses.append('status = ?')
        params.append(status)
    sql = "SELECT id, code, name, equipment_type, description, status, brand, model FROM inventory_equipment WHERE " + ' AND '.join(clauses) + " ORDER BY code LIMIT 80"
    return [
        {'id': str(r.get('id')), 'code': r.get('code') or '', 'label': r.get('name') or '', 'type': 'consommable' if r.get('equipment_type') == 'consumable' else (resource_type or 'outil'), 'extra': ' · '.join([x for x in [r.get('brand') or '', r.get('model') or '', r.get('status') or '', r.get('description') or ''] if x])}
        for r in _sqlite_rows(db, sql, params)
    ]


def _resource_search_pedashop(q, resource_type='', status=''):
    db = os.environ.get('TPMANAGER_PEDASHOP_DB', '/data/pedashop/pedashop.sqlite3')
    like = f'%{q or ""}%'
    sql = """
        SELECT a.id, a.reference_interne, a.designation, a.categorie, a.sous_categorie, a.unite,
               COALESCE(SUM(s.stock_reel - s.stock_reserve_demande - s.stock_en_preparation), 0) AS stock_dispo
        FROM pedashop_article a
        LEFT JOIN pedashop_stockarticlemagasin s ON s.article_id = a.id
        WHERE (a.reference_interne LIKE ? OR a.designation LIKE ? OR a.categorie LIKE ? OR a.sous_categorie LIKE ? OR a.description LIKE ?)
          AND COALESCE(a.archive, 0) = 0
        GROUP BY a.id
        ORDER BY a.reference_interne
        LIMIT 80
    """
    return [
        {'id': str(r.get('id')), 'code': r.get('reference_interne') or '', 'label': r.get('designation') or '', 'type': 'consommable' if resource_type != 'materiel' else 'materiel', 'extra': ' · '.join([x for x in [r.get('categorie') or '', r.get('sous_categorie') or '', f"stock dispo {r.get('stock_dispo')} {r.get('unite') or ''}"] if x])}
        for r in _sqlite_rows(db, sql, (like, like, like, like, like))
    ]


def _resource_search_system(q, resource_type='', status=''):
    # D'abord la copie synchronisée interne, puis la base System Manager si montée.
    local_qs = SystemePedagogiqueRef.objects.filter(actif=True)
    if q:
        local_qs = local_qs.filter(Q(code__icontains=q) | Q(designation__icontains=q) | Q(zone_nom__icontains=q) | Q(statut__icontains=q))
    if status:
        local_qs = local_qs.filter(statut=status)
    local = [
        {'id': str(s.system_manager_id or s.id), 'code': s.code, 'label': s.designation, 'type': 'systeme', 'extra': ' · '.join([x for x in [s.zone_nom or '', s.statut or ''] if x])}
        for s in local_qs.order_by('zone_code', 'code')[:80]
    ]
    if local:
        return local
    db = os.environ.get('TPMANAGER_SYSTEM_MANAGER_DB', '/data/system-manager/system-manager.sqlite3')
    like = f'%{q or ""}%'
    clauses = ['(sys.code LIKE ? OR sys.designation LIKE ? OR sys.description LIKE ? OR COALESCE(z.nom, "") LIKE ? OR COALESCE(sz.nom, "") LIKE ?)']
    params = [like, like, like, like, like]
    if status:
        clauses.append('sys.statut = ?')
        params.append(status)
    sql = """
        SELECT sys.id, sys.code, sys.designation, sys.statut, COALESCE(z.nom, '') AS zone_nom, COALESCE(sz.nom, '') AS sous_zone_nom
        FROM system_manager_educationalsystem sys
        LEFT JOIN system_manager_workshopzone z ON z.id = sys.zone_id
        LEFT JOIN system_manager_workshopsubzone sz ON sz.id = sys.sous_zone_id
        WHERE {where}
        ORDER BY z.code, sys.code
        LIMIT 80
    """.format(where=' AND '.join(clauses))
    return [
        {'id': str(r.get('id')), 'code': r.get('code') or '', 'label': r.get('designation') or '', 'type': 'systeme', 'extra': ' · '.join([x for x in [r.get('zone_nom') or '', r.get('sous_zone_nom') or '', r.get('statut') or ''] if x])}
        for r in _sqlite_rows(db, sql, params)
    ]


def api_resource_search(request):
    source = (request.GET.get('source') or '').strip()
    q = (request.GET.get('q') or '').strip()
    resource_type = (request.GET.get('type') or '').strip()
    status = (request.GET.get('status') or '').strip()
    if source == 'manual':
        return JsonResponse({'results': []})
    if source == 'toolmag':
        results = _resource_search_toolmag(q, resource_type, status)
    elif source == 'pedashop':
        results = _resource_search_pedashop(q, resource_type, status)
    elif source == 'system_manager':
        results = _resource_search_system(q, resource_type, status)
    else:
        results = []
    return JsonResponse({'results': results})


def api_diplome_refs(request, diplome_pk):
    diplome = get_object_or_404(BacDiplome, pk=diplome_pk, actif=True)
    competences = [{'id': c.id, 'code': c.code, 'libelle': c.libelle_officiel} for c in diplome.competences_officielles.filter(selectable_bac=True).order_by('code')]
    champs = []
    for champ in diplome.champs_tp.filter(actif=True).order_by('phase', 'ordre'):
        champs.append({
            'id': champ.id, 'code': champ.code, 'libelle': champ.libelle,
            'type': champ.type_champ, 'obligatoire': champ.obligatoire,
            'options': [{'valeur': o.valeur, 'libelle': o.libelle} for o in champ.options.all()],
        })
    
    activities = []
    for a in diplome.activites_officielles.prefetch_related('taches__competences_liees__competence').order_by('ordre', 'code'):
        activities.append({'id': a.id, 'code': a.code, 'libelle': a.libelle_officiel, 'taches': [
            {'id': t.id, 'code': t.code, 'libelle': t.libelle_officiel, 'autonomie': t.get_autonomie_display(), 'responsabilite': t.responsabilite_resume, 'competences': [{'id': l.competence_id, 'code': l.competence.code, 'poids': l.poids} for l in t.competences_liees.select_related('competence').all()]}
            for t in a.taches.all().order_by('ordre', 'code')
        ]})
    return JsonResponse({'diplome': diplome.code, 'competences': competences, 'champs': champs, 'activites': activities})
