from __future__ import annotations
from collections import defaultdict
from datetime import date
from django.db.models import Count
from django.shortcuts import get_object_or_404, render
from tp_manager.models import TpUser
from .models import EvalActivity, EvalCriterionResult, EvalBilanIntermediaire, EvalLevel, LEVEL_COLORS


def _student_queryset():
    return TpUser.objects.filter(active=True).exclude(role_principal__in=['professeur', 'admin', 'admin_suite']).order_by('class_name', 'last_name', 'first_name')


def dashboard(request):
    students = _student_queryset().annotate(eval_count=Count('eval_activities')).filter(eval_count__gt=0)
    classes = EvalActivity.objects.values('classe', 'formation_code').annotate(count=Count('id')).order_by('formation_code', 'classe')
    context = {
        'students': students[:50],
        'classes': classes,
        'activity_count': EvalActivity.objects.count(),
        'result_count': EvalCriterionResult.objects.count(),
        'bilan_count': EvalBilanIntermediaire.objects.count(),
    }
    return render(request, 'evaluation_manager/dashboard.html', context)


def class_dashboard(request):
    formation = request.GET.get('formation', '').strip()
    classe = request.GET.get('classe', '').strip()
    q = EvalActivity.objects.select_related('eleve', 'tp').prefetch_related('criteria_results__critere__competence')
    if formation:
        q = q.filter(formation_code=formation)
    if classe:
        q = q.filter(classe=classe)
    students = {}
    competence_counts = defaultdict(lambda: defaultdict(int))
    for activity in q:
        students[activity.eleve_id] = activity.eleve
        for result in activity.criteria_results.all():
            comp = result.critere.competence
            competence_counts[comp][result.niveau_prof_effectif()] += 1
    context = {
        'formation': formation,
        'classe': classe,
        'classes': EvalActivity.objects.exclude(classe='').values_list('formation_code', 'classe').distinct().order_by('formation_code', 'classe'),
        'students': sorted(students.values(), key=lambda s: (s.last_name, s.first_name, s.code)),
        'competence_counts': sorted(competence_counts.items(), key=lambda item: item[0].code),
        'level_colors': LEVEL_COLORS,
    }
    return render(request, 'evaluation_manager/class_dashboard.html', context)


def student_dashboard(request, eleve_pk):
    eleve = get_object_or_404(TpUser, pk=eleve_pk)
    mode = request.GET.get('mode', 'compact')

    activities = list(
        EvalActivity.objects.filter(eleve=eleve)
        .select_related('tp')
        .prefetch_related('criteria_results__critere__competence')
        .order_by('date_activite', 'code_eval')
    )
    bilans = list(
        EvalBilanIntermediaire.objects.filter(eleve=eleve)
        .prefetch_related('competence_results__competence')
        .order_by('date_bilan')
    )

    columns = _build_columns(activities, bilans)
    column_groups = _build_column_groups(columns)

    results_by_activity = defaultdict(dict)
    criteria_by_comp = defaultdict(dict)
    for activity in activities:
        for result in activity.criteria_results.all():
            comp = result.critere.competence
            results_by_activity[activity.id][result.critere_id] = result
            criteria_by_comp[comp][result.critere_id] = result.critere

    bilan_by_comp = {}
    for bilan in bilans:
        for result in bilan.competence_results.all():
            bilan_by_comp[(bilan.id, result.competence_id)] = result

    compact_rows = []
    for comp, criteria_map in sorted(criteria_by_comp.items(), key=lambda x: x[0].code):
        row = {'competence': comp, 'col_levels': []}
        for col in columns:
            if col['kind'] == 'activity':
                activity = col['obj']
                levels = []
                for crit_id in criteria_map:
                    r = results_by_activity.get(activity.id, {}).get(crit_id)
                    if r:
                        levels.append(r.niveau_prof_effectif())
                row['col_levels'].append(_synth_level(levels))
            else:
                br = bilan_by_comp.get((col['obj'].id, comp.id))
                row['col_levels'].append(br.niveau if br else '')
        compact_rows.append(row)

    detail_rows = []
    for comp, criteria_map in sorted(criteria_by_comp.items(), key=lambda x: x[0].code):
        # Ligne compétence : les bilans se positionnent ici uniquement, pas sur les sous-compétences.
        comp_row = {'type': 'competence', 'competence': comp, 'critere': None, 'col_levels': []}
        for col in columns:
            if col['kind'] == 'bilan':
                br = bilan_by_comp.get((col['obj'].id, comp.id))
                comp_row['col_levels'].append(br.niveau if br else '')
            else:
                comp_row['col_levels'].append('')
        detail_rows.append(comp_row)
        for crit in sorted(criteria_map.values(), key=lambda c: (c.ordre, c.code)):
            row = {'type': 'critere', 'competence': comp, 'critere': crit, 'col_levels': []}
            for col in columns:
                if col['kind'] == 'activity':
                    r = results_by_activity.get(col['obj'].id, {}).get(crit.id)
                    row['col_levels'].append(r.niveau_prof_effectif() if r else '')
                else:
                    row['col_levels'].append('')
            detail_rows.append(row)

    context = {
        'eleve': eleve,
        'mode': mode,
        'activities': activities,
        'bilans': bilans,
        'columns': columns,
        'column_groups': column_groups,
        'compact_rows': compact_rows,
        'detail_rows': detail_rows,
        'level_colors': LEVEL_COLORS,
        'levels': EvalLevel.choices,
    }
    return render(request, 'evaluation_manager/student_dashboard.html', context)


def _build_columns(activities, bilans):
    columns = []
    for activity in activities:
        columns.append({
            'kind': 'activity',
            'obj': activity,
            'date': activity.date_activite,
            'year_label': _year_label(activity.classe, activity.formation_code, activity.date_activite),
            'display_code': activity.code_eval or (activity.tp.code if activity.tp_id else 'EV'),
            'short_date': activity.date_activite.strftime('%d/%m') if activity.date_activite else '',
            'is_bilan': False,
        })
    for bilan in bilans:
        columns.append({
            'kind': 'bilan',
            'obj': bilan,
            'date': bilan.date_bilan,
            'year_label': _year_label(bilan.classe, bilan.formation_code, bilan.date_bilan),
            'display_code': bilan.nom,
            'short_date': bilan.date_bilan.strftime('%d/%m') if bilan.date_bilan else '',
            'is_bilan': True,
        })
    return sorted(columns, key=lambda c: (c['date'] or date.min, 1 if c['kind'] == 'bilan' else 0, c['display_code']))


def _build_column_groups(columns):
    groups = []
    for col in columns:
        label = col.get('year_label') or 'Année non renseignée'
        if groups and groups[-1]['label'] == label:
            groups[-1]['count'] += 1
        else:
            groups.append({'label': label, 'count': 1})
    return groups


def _year_label(classe: str, formation: str = '', d=None):
    raw = f'{classe or ""} {formation or ""}'.upper().replace('È', 'E').replace('É', 'E')
    raw = raw.replace('ÈRE', 'ERE').replace('TERMINALE', 'TALE')
    if any(x in raw for x in ['2NDE', 'SECONDE', '2MTNE', '2MELEC', '2CIEL', '2MFER']):
        return '2nde'
    if any(x in raw for x in ['1ERE ANNEE', '1RE ANNEE', '1ER ANNEE', 'FED1', 'STEL1', 'BTS1', 'CAP1']):
        return '1ère année'
    if any(x in raw for x in ['2EME ANNEE', '2E ANNEE', 'FED2', 'STEL2', 'BTS2', 'CAP2']):
        return '2ème année'
    if any(x in raw for x in ['1MELEC', '1CIEL', '1MFER', '1 MELEC', '1 CIEL', '1 MFER', 'PREMIERE', '1ERE', '1RE']):
        return '1ère'
    if any(x in raw for x in ['TMELEC', 'TCIEL', 'TMFER', 'T MELEC', 'T CIEL', 'T MFER', 'TALE', 'TERM']):
        return 'Tale'
    if d:
        return str(getattr(d, 'year', ''))
    return 'Année non renseignée'


def _synth_level(levels):
    if not levels:
        return ''
    if all(l == EvalLevel.AB for l in levels):
        return EvalLevel.AB
    values = [l for l in levels if l not in {'', EvalLevel.NE, EvalLevel.AB}]
    if not values:
        return EvalLevel.NE
    priority = {EvalLevel.NA: 1, EvalLevel.EC: 2, EvalLevel.A: 3, EvalLevel.PA: 4}
    return min(values, key=lambda l: priority.get(l, 99))


def activity_detail(request, pk):
    activity = get_object_or_404(EvalActivity.objects.select_related('eleve', 'tp'), pk=pk)
    results = activity.criteria_results.select_related('critere__competence').order_by('critere__competence__code', 'critere__ordre')
    context = {'activity': activity, 'results': results, 'level_colors': LEVEL_COLORS}
    return render(request, 'evaluation_manager/activity_detail.html', context)


def bilan_detail(request, pk):
    bilan = get_object_or_404(EvalBilanIntermediaire.objects.select_related('eleve'), pk=pk)
    results = bilan.competence_results.select_related('competence').order_by('competence__code')
    context = {'bilan': bilan, 'results': results, 'level_colors': LEVEL_COLORS}
    return render(request, 'evaluation_manager/bilan_detail.html', context)
