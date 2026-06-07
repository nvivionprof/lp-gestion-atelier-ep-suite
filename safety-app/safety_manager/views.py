from __future__ import annotations
from django.contrib import messages
from django.conf import settings
from django.db.models import Count, Q, Max
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from .models import (
    SafetyUser, SafetyZone, WorkUnit, RiskFamily, RiskAssessment, PreventionAction, SafetyEvent, EventFact,
    CauseAnalysis, FiveWhyLine, IshikawaCause, CauseTreeNode, CauseTreeLink, DangerousSituation
)
from .forms import (
    SafetyZoneForm, WorkUnitForm, RiskAssessmentForm, PreventionActionForm, SafetyEventQuickForm, PublicSafetyEventForm,
    EventFactForm, CauseAnalysisForm, FiveWhyLineForm, IshikawaCauseForm, CauseTreeNodeForm, CauseTreeLinkForm, DangerousSituationForm
)
from .permissions import safety_login_required, safety_edit_required, safety_declare_required, safety_admin_required, current_safety_user
from .exports import export_duerp_pdf, export_actions_csv, export_risks_csv, export_event_pdf, export_events_pdf
from .sync import sync_users_from_lp_core



# --- LP Suite SSO portal-login V0.1.0 ---
def _portal_token_payload(request):
    from django.core import signing
    try:
        return signing.loads(
            request.GET.get('token') or '',
            key=getattr(settings, 'LP_CORE_API_TOKEN', ''),
            salt='lp-suite-sso',
            max_age=120,
        )
    except Exception:
        return None

def portal_login(request):
    payload = _portal_token_payload(request)
    if not payload:
        messages.error(request, 'Connexion LP Core impossible ou expirée. Merci de te reconnecter.')
        return redirect('safety_login')
    code = (payload.get('code') or '').strip()
    username = (payload.get('username') or '').strip()
    user = SafetyUser.objects.filter(Q(code=code) | Q(username=username), active=True).first()
    if not user:
        messages.error(request, 'Compte LP Core non synchronisé dans Safety Manager.')
        return redirect('safety_login')
    request.session['safety_user_id'] = user.id
    messages.success(request, f'Connexion Safety via LP Core : {user.first_name} {user.last_name}.')
    return redirect('safety_dashboard')

@require_http_methods(['GET', 'POST'])
def login_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = SafetyUser.objects.filter(username=username, active=True).first() or SafetyUser.objects.filter(code=username, active=True).first()
        if user and user.check_password(password):
            request.session['safety_user_id'] = user.id
            messages.success(request, f'Connexion Safety : {user.first_name} {user.last_name}.')
            return redirect('safety_dashboard')
        messages.error(request, 'Identifiant ou mot de passe incorrect. Synchronisez depuis LP Core si nécessaire.')
    return render(request, 'safety_manager/login.html')


def logout_view(request):
    request.session.pop('safety_user_id', None)
    messages.success(request, 'Déconnexion Safety effectuée.')
    return redirect('safety_login')


def _internal_sync_authorized(request):
    expected = getattr(settings, 'LP_CORE_API_TOKEN', '') or ''
    provided = request.headers.get('X-API-Key') or request.POST.get('token') or request.GET.get('token') or ''
    return bool(expected and provided == expected)


@csrf_exempt
@require_http_methods(['POST'])
def sync_users_view(request):
    internal = _internal_sync_authorized(request)
    if internal:
        try:
            force_password = request.POST.get('force_password') in {'1', 'true', 'True', 'oui', 'OUI'}
            core_user_id = request.POST.get('core_user_id') or request.GET.get('core_user_id')
            report = sync_users_from_lp_core(timeout=90, force_password=force_password, core_user_id=core_user_id)
            return JsonResponse({'ok': len(report.get('errors', [])) == 0, 'report': report})
        except Exception as exc:
            return JsonResponse({'ok': False, 'error': str(exc)}, status=500)
    user = current_safety_user(request)
    if not user or not user.is_admin_like:
        messages.error(request, 'Synchronisation Safety réservée aux administrateurs.')
        return redirect('safety_login')
    try:
        report = sync_users_from_lp_core(timeout=90)
        if report['errors']:
            messages.warning(request, f"Synchronisation Safety partielle : {report['created']} créés, {report['updated']} mis à jour, {len(report['errors'])} erreurs.")
        else:
            messages.success(request, f"Synchronisation Safety terminée : {report['created']} créés, {report['updated']} mis à jour.")
    except Exception as exc:
        messages.error(request, f'Échec synchronisation LP Core → Safety : {exc}')
    return redirect('safety_dashboard')



def _filter_qs(queryset, request, *fields):
    q = (request.GET.get('q') or '').strip()
    if q:
        condition = Q()
        for field in fields:
            condition |= Q(**{f'{field}__icontains': q})
        queryset = queryset.filter(condition)
    return queryset, q


def _display_priority_counts():
    """Calcule les 3 priorités Safety affichées sur écran atelier."""
    counts = {1: 0, 2: 0, 3: 0}
    for risk in RiskAssessment.objects.exclude(statut='archive'):
        priority = int(risk.priorite_calculee or 3)
        if priority <= 1:
            counts[1] += 1
        elif priority == 2:
            counts[2] += 1
        else:
            counts[3] += 1
    for sit in DangerousSituation.objects.exclude(statut='archivee'):
        priority = int(sit.priorite or 3)
        if priority <= 1:
            counts[1] += 1
        elif priority == 2:
            counts[2] += 1
        else:
            counts[3] += 1
    return counts


def _public_safety_metrics():
    """Regroupe les indicateurs publics sans données personnelles sensibles."""
    today = timezone.localdate()
    year_start = today.replace(month=1, day=1)
    last_accident_date = SafetyEvent.objects.filter(type_evenement='accident').aggregate(last=Max('date'))['last']
    if last_accident_date:
        days_without_accident = max(0, (today - last_accident_date).days)
    else:
        days_without_accident = (today - year_start).days + 1
    accidents_year = SafetyEvent.objects.filter(type_evenement='accident', date__gte=year_start).count()
    near_misses_year = SafetyEvent.objects.filter(type_evenement='presqu_accident', date__gte=year_start).count()
    open_events = SafetyEvent.objects.exclude(statut_analyse='cloture').count()
    priority_counts = _display_priority_counts()
    late_actions = PreventionAction.objects.filter(echeance__lt=today).exclude(statut__in=['realisee', 'verifiee', 'abandonnee']).count()
    current_actions = PreventionAction.objects.filter(statut__in=['a_etudier', 'validee', 'en_cours']).count()
    done_actions = PreventionAction.objects.filter(statut__in=['realisee', 'verifiee']).count()
    return {
        'today': today,
        'days_without_accident': days_without_accident,
        'record_days_without_accident': max(days_without_accident, 0),
        'accidents_year': accidents_year,
        'near_misses_year': near_misses_year,
        'open_events': open_events,
        'priority_counts': priority_counts,
        'p1_count': priority_counts.get(1, 0),
        'p2_count': priority_counts.get(2, 0),
        'p3_count': priority_counts.get(3, 0),
        'actions_late': late_actions,
        'actions_current': current_actions,
        'actions_done': done_actions,
        'sst_users': SafetyUser.objects.filter(active=True).filter(Q(rights__icontains='SST') | Q(role_principal__icontains='sst'))[:6],
        'last_update': timezone.now(),
    }


def public_dashboard(request):
    """Tableau de bord public Safety Manager.

    Accessible sans connexion pour un écran d'accueil ou un poste atelier.
    Les informations personnelles détaillées restent réservées à l'interface
    connectée.
    """
    return render(request, 'safety_manager/public_dashboard.html', _public_safety_metrics())


def public_display(request):
    """Affichage dynamique grand écran inspiré des panneaux sécurité atelier."""
    return render(request, 'safety_manager/public_display.html', _public_safety_metrics())


def safety_instructions(request):
    """Tableau réglementaire public de consignes sécurité."""
    return render(request, 'safety_manager/safety_instructions.html', _public_safety_metrics())


@require_http_methods(['GET', 'POST'])
def public_event_create(request):
    messages.warning(request, 'La déclaration sans connexion est désactivée. Connectez-vous pour déclarer un événement.')
    return redirect('safety_login')


def public_event_thanks(request, code):
    return render(request, 'safety_manager/public_event_thanks.html', {'code': code})


@safety_login_required
def dashboard(request):
    today = timezone.localdate()
    month_start = today.replace(day=1)
    risks_by_priority = RiskAssessment.objects.values('priorite_calculee').annotate(count=Count('id')).order_by('priorite_calculee')
    events_period = SafetyEvent.objects.filter(date__gte=month_start)
    context = {
        'risk_total': RiskAssessment.objects.count(),
        'priority1_count': RiskAssessment.objects.filter(priorite_calculee=1, statut__in=['brouillon', 'valide', 'a_revoir']).count(),
        'actions_late': PreventionAction.objects.filter(echeance__lt=today).exclude(statut__in=['realisee', 'verifiee', 'abandonnee']).count(),
        'actions_open': PreventionAction.objects.exclude(statut__in=['realisee', 'verifiee', 'abandonnee']).count(),
        'events_month': events_period.count(),
        'recent_events': SafetyEvent.objects.select_related('zone', 'personne_concernee').order_by('-date', '-created_at')[:8],
        'critical_risks': RiskAssessment.objects.select_related('unite_travail', 'famille_risque').filter(priorite_calculee=1).order_by('-updated_at')[:8],
        'due_actions': PreventionAction.objects.select_related('responsable').exclude(statut__in=['realisee', 'verifiee', 'abandonnee']).order_by('echeance')[:8],
        'families_stats': RiskAssessment.objects.values('famille_risque__nom').annotate(count=Count('id')).order_by('-count')[:10],
        'zones_stats': SafetyEvent.objects.values('zone__nom').annotate(count=Count('id')).order_by('-count')[:10],
        'risks_by_priority': list(risks_by_priority),
    }
    return render(request, 'safety_manager/dashboard.html', context)


@safety_login_required
def zone_list(request):
    zones, q = _filter_qs(SafetyZone.objects.all(), request, 'code', 'nom', 'description')
    return render(request, 'safety_manager/zone_list.html', {'zones': zones, 'q': q})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def zone_create(request):
    form = SafetyZoneForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Zone créée.'); return redirect('safety_zone_list')
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Créer une zone Safety'})


@safety_login_required
def workunit_list(request):
    units, q = _filter_qs(WorkUnit.objects.select_related('zone', 'responsable'), request, 'code', 'nom', 'description')
    return render(request, 'safety_manager/workunit_list.html', {'units': units, 'q': q})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def workunit_create(request):
    form = WorkUnitForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Unité de travail créée.'); return redirect('safety_workunit_list')
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Créer une unité de travail'})


@safety_login_required
def risk_list(request):
    risks = RiskAssessment.objects.select_related('unite_travail', 'famille_risque', 'responsable_suivi')
    q = (request.GET.get('q') or '').strip()
    priority = request.GET.get('priorite') or ''
    status = request.GET.get('statut') or ''
    family = request.GET.get('famille') or ''
    if q:
        risks = risks.filter(Q(code__icontains=q) | Q(danger__icontains=q) | Q(situation_dangereuse__icontains=q) | Q(dommage_potentiel__icontains=q))
    if priority:
        risks = risks.filter(priorite_calculee=priority)
    if status:
        risks = risks.filter(statut=status)
    if family:
        risks = risks.filter(famille_risque_id=family)
    context = {'risks': risks[:500], 'q': q, 'families': RiskFamily.objects.filter(actif=True), 'priority': priority, 'status': status, 'family': family}
    return render(request, 'safety_manager/risk_list.html', context)


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def risk_create(request):
    user = current_safety_user(request)
    form = RiskAssessmentForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        risk = form.save(commit=False)
        risk.redacteur = user
        risk.save(); messages.success(request, f'Risque {risk.code} créé. Priorité calculée : P{risk.priorite_calculee}.')
        return redirect('safety_risk_detail', risk.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Créer une évaluation de risque'})


@safety_login_required
def risk_detail(request, pk):
    risk = get_object_or_404(RiskAssessment.objects.select_related('unite_travail', 'famille_risque', 'responsable_suivi'), pk=pk)
    actions = risk.actions.select_related('responsable').all()
    return render(request, 'safety_manager/risk_detail.html', {'risk': risk, 'actions': actions})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def risk_update(request, pk):
    risk = get_object_or_404(RiskAssessment, pk=pk)
    form = RiskAssessmentForm(request.POST or None, instance=risk)
    if request.method == 'POST' and form.is_valid():
        risk = form.save(); messages.success(request, f'Risque {risk.code} mis à jour.'); return redirect('safety_risk_detail', risk.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': f'Modifier {risk.code}'})


@safety_edit_required
def risk_duplicate(request, pk):
    src = get_object_or_404(RiskAssessment, pk=pk)
    if request.method == 'POST':
        src.pk = None; src.id = None; src.code = ''; src.statut = 'brouillon'; src.validateur = None; src.historique = f'Dupliqué depuis {get_object_or_404(RiskAssessment, pk=pk).code}.'; src.save()
        messages.success(request, f'Risque dupliqué : {src.code}.')
        return redirect('safety_risk_detail', src.pk)
    return render(request, 'safety_manager/confirm.html', {'title': f'Dupliquer {src.code}', 'message': 'Créer un nouveau risque indépendant à partir de ce modèle ?'})


@safety_login_required
def action_list(request):
    actions = PreventionAction.objects.select_related('responsable', 'risk_assessment', 'event')
    q = (request.GET.get('q') or '').strip()
    if q:
        actions = actions.filter(Q(code__icontains=q) | Q(titre__icontains=q) | Q(description__icontains=q))
    return render(request, 'safety_manager/action_list.html', {'actions': actions[:500], 'q': q})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def action_create(request):
    initial = {}
    origin_label = ''
    if request.GET.get('risk'):
        initial['risk_assessment'] = request.GET.get('risk'); initial['origine'] = 'duerp'; origin_label = 'risque DUERP'
    if request.GET.get('event'):
        initial['event'] = request.GET.get('event'); initial['origine'] = 'incident'; origin_label = 'événement'
    if request.GET.get('situation'):
        initial['dangerous_situation'] = request.GET.get('situation'); initial['origine'] = 'observation'; origin_label = 'situation dangereuse'
    if not initial:
        messages.error(request, 'Une action doit être créée depuis un événement, un risque DUERP ou une situation dangereuse.')
        return redirect('safety_action_list')
    form = PreventionActionForm(request.POST or None, request.FILES or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        action = form.save(); messages.success(request, f'Action {action.code} créée.'); return redirect('safety_action_list')
    return render(request, 'safety_manager/form.html', {'form': form, 'title': f'Créer une action depuis {origin_label}'})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def action_update(request, pk):
    action = get_object_or_404(PreventionAction, pk=pk)
    form = PreventionActionForm(request.POST or None, request.FILES or None, instance=action)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, f'Action {action.code} mise à jour.'); return redirect('safety_action_list')
    return render(request, 'safety_manager/form.html', {'form': form, 'title': f'Modifier {action.code}'})


@safety_login_required
def event_list(request):
    events = SafetyEvent.objects.select_related('zone', 'unite_travail', 'personne_concernee')
    q = (request.GET.get('q') or '').strip()
    if q:
        events = events.filter(Q(code__icontains=q) | Q(description_courte__icontains=q) | Q(recit_detaille__icontains=q) | Q(materiel_implique__icontains=q))
    return render(request, 'safety_manager/event_list.html', {'events': events[:500], 'q': q})


@safety_declare_required
@require_http_methods(['GET', 'POST'])
def event_create(request):
    user = current_safety_user(request)
    class_filter = request.GET.get('classe') or request.POST.get('classe_ou_groupe') or ''
    form = SafetyEventQuickForm(request.POST or None, class_filter=class_filter)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False); event.created_by = user; event.updated_by = user; event.save()
        messages.success(request, f'Événement {event.code} déclaré.')
        return redirect('safety_event_detail', event.pk)
    return render(request, 'safety_manager/event_form.html', {'form': form, 'title': 'Déclarer un accident / incident / presqu’accident'})


@safety_login_required
def event_detail(request, pk):
    event = get_object_or_404(SafetyEvent.objects.select_related('zone', 'unite_travail', 'personne_concernee'), pk=pk)
    return render(request, 'safety_manager/event_detail.html', {'event': event})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def event_update(request, pk):
    event = get_object_or_404(SafetyEvent, pk=pk)
    form = SafetyEventQuickForm(request.POST or None, instance=event)
    if request.method == 'POST' and form.is_valid():
        event = form.save(commit=False); event.updated_by = current_safety_user(request); event.save()
        messages.success(request, f'Événement {event.code} mis à jour.'); return redirect('safety_event_detail', event.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': f'Modifier {event.code}'})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def fact_create(request, pk):
    event = get_object_or_404(SafetyEvent, pk=pk)
    form = EventFactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        fact = form.save(commit=False); fact.event = event; fact.save()
        messages.success(request, 'Fait ajouté.'); return redirect('safety_event_detail', event.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': f'Ajouter un fait — {event.code}'})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def analysis_create(request, pk):
    event = get_object_or_404(SafetyEvent, pk=pk)
    form = CauseAnalysisForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        analysis = form.save(commit=False); analysis.event = event; analysis.save()
        if analysis.methode == '5_pourquoi' and not analysis.fivewhy_lines.exists():
            for i in range(1, 6):
                FiveWhyLine.objects.create(analysis=analysis, ordre=i, question=f'Pourquoi ? #{i}')
        messages.success(request, 'Analyse causale créée.'); return redirect('safety_analysis_detail', analysis.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': f'Créer une analyse — {event.code}'})


@safety_login_required
def analysis_detail(request, pk):
    analysis = get_object_or_404(CauseAnalysis.objects.select_related('event'), pk=pk)
    return render(request, 'safety_manager/analysis_detail.html', {'analysis': analysis})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def fivewhy_add(request, pk):
    analysis = get_object_or_404(CauseAnalysis, pk=pk)
    form = FiveWhyLineForm(request.POST or None, initial={'ordre': analysis.fivewhy_lines.count() + 1})
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False); obj.analysis = analysis; obj.save(); return redirect('safety_analysis_detail', analysis.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Ajouter une ligne 5 pourquoi'})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def ishikawa_add(request, pk):
    analysis = get_object_or_404(CauseAnalysis, pk=pk)
    form = IshikawaCauseForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False); obj.analysis = analysis; obj.save(); return redirect('safety_analysis_detail', analysis.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Ajouter une cause Ishikawa'})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def tree_node_add(request, pk):
    analysis = get_object_or_404(CauseAnalysis, pk=pk)
    form = CauseTreeNodeForm(request.POST or None)
    form.fields['fact'].queryset = analysis.event.facts.all()
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False); obj.analysis = analysis; obj.save(); return redirect('safety_analysis_detail', analysis.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Ajouter un nœud arbre des causes'})


@safety_edit_required
@require_http_methods(['GET', 'POST'])
def tree_link_add(request, pk):
    analysis = get_object_or_404(CauseAnalysis, pk=pk)
    form = CauseTreeLinkForm(request.POST or None)
    form.fields['source_node'].queryset = analysis.tree_nodes.all()
    form.fields['target_node'].queryset = analysis.tree_nodes.all()
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False); obj.analysis = analysis; obj.save(); return redirect('safety_analysis_detail', analysis.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Ajouter un lien arbre des causes'})


@safety_login_required
def export_duerp_pdf_view(request):
    return export_duerp_pdf(request)


@safety_login_required
def export_actions_csv_view(request):
    return export_actions_csv(request)


@safety_login_required
def export_risks_csv_view(request):
    return export_risks_csv(request)


@safety_login_required
def export_event_pdf_view(request, pk):
    event = get_object_or_404(SafetyEvent, pk=pk)
    return export_event_pdf(request, event)


@safety_login_required
def api_dashboard(request):
    return JsonResponse({
        'risks_total': RiskAssessment.objects.count(),
        'priority1': RiskAssessment.objects.filter(priorite_calculee=1).count(),
        'actions_open': PreventionAction.objects.exclude(statut__in=['realisee', 'verifiee', 'abandonnee']).count(),
        'events_total': SafetyEvent.objects.count(),
    })



@safety_login_required
def situation_list(request):
    situations = DangerousSituation.objects.select_related('zone', 'unite_travail', 'famille_risque')
    q = (request.GET.get('q') or '').strip()
    duerp = request.GET.get('duerp') or ''
    if q:
        situations = situations.filter(Q(code__icontains=q) | Q(titre__icontains=q) | Q(description__icontains=q))
    if duerp in {'0', '1'}:
        situations = situations.filter(inclure_duerp=(duerp == '1'))
    return render(request, 'safety_manager/situation_list.html', {'situations': situations[:500], 'q': q, 'duerp': duerp})


@safety_declare_required
@require_http_methods(['GET', 'POST'])
def situation_create(request):
    user = current_safety_user(request)
    form = DangerousSituationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.declaree_par = user
        obj.save()
        messages.success(request, f'Situation dangereuse {obj.code} déclarée.')
        return redirect('safety_situation_detail', obj.pk)
    return render(request, 'safety_manager/form.html', {'form': form, 'title': 'Déclarer une situation dangereuse'})


@safety_login_required
def situation_detail(request, pk):
    situation = get_object_or_404(DangerousSituation.objects.select_related('zone', 'unite_travail', 'famille_risque', 'risk_assessment'), pk=pk)
    return render(request, 'safety_manager/situation_detail.html', {'situation': situation})


@safety_login_required
def export_events_pdf_view(request):
    return export_events_pdf(request)


# --- Administration SQL base module ---
def sql_database_admin(request):
    from .permissions import safety_admin_required
    from .db_sql_admin import render_sql_admin
    @safety_admin_required
    def _view(req):
        return render_sql_admin(req, 'safety_manager/sql_database.html', 'Safety Manager')
    return _view(request)


def sql_database_export(request):
    from .permissions import safety_admin_required
    from .db_sql_admin import export_sql_response
    @safety_admin_required
    def _view(req):
        return export_sql_response(req, 'safety')
    return _view(request)


def sql_database_import(request):
    from .permissions import safety_admin_required
    from .db_sql_admin import import_sql_response
    @safety_admin_required
    def _view(req):
        return import_sql_response(req, 'safety_manager/sql_database.html', 'Safety Manager', 'safety')
    return _view(request)

def help_view(request):
    return render(request, 'safety_manager/help.html')


def about_view(request):
    return render(request, 'safety_manager/about.html')
