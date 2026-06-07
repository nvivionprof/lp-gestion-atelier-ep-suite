from __future__ import annotations
from datetime import datetime, timedelta, time
from io import BytesIO
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden, FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import qrcode
import zipfile
from pathlib import Path
from .models import (
    SystemUser, Formation, Niveau, SchoolClass, WorkshopZone, WorkshopSubZone, EducationalSystem, DocumentCategory,
    SystemDocument, DefaultCheckTemplate, CheckItem, ReservationGroup, Reservation, WorkSession, CheckResponse, SystemAnomaly, WorkshopBlock, WorkshopBlockSlot, SystemTPAssociation, SystemSafetyLink, MaintenanceIntervention, MaintenanceCheckLine, MaintenanceDrawingZone, SystemChangeLog, TemporarySystemPermission
)
from .forms import (
    ZoneForm, SubZoneForm, FormationForm, NiveauForm, EducationalSystemForm, DocumentCategoryForm, SystemDocumentForm, DefaultCheckTemplateForm,
    CheckItemForm, ReservationForm, QuickReservationForm, WorkSessionStartForm, WorkSessionReturnForm, SystemAnomalyForm, WorkshopBlockForm, WorkshopBlockSlotForm, SystemTPAssociationForm, SystemSafetyLinkForm, MaintenanceInterventionForm, MaintenanceCheckLineForm, MaintenanceDrawingZoneForm, SystemChangeLogForm, TemporarySystemPermissionForm, ReservationGroupForm, SystemSearchForm
)
from .permissions import system_login_required, system_edit_required, system_admin_required, current_system_user, can_create_systems, can_edit_systems
from .sync import sync_users_from_lp_core, sync_formations_from_lp_core, sync_classes_from_lp_core, sync_workshop_blocks_from_lp_core, sync_workshop_zones_from_lp_core, push_workshop_referentials_to_lp_core
from .services import week_bounds, current_reservation_for_system, upcoming_reservations, system_effective_status


def _filter_qs(queryset, request, *fields):
    q = (request.GET.get('q') or '').strip()
    if q:
        condition = Q()
        for field in fields:
            condition |= Q(**{f'{field}__icontains': q})
        queryset = queryset.filter(condition)
    return queryset, q


@require_http_methods(['GET', 'POST'])


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
        return redirect('system_login')
    code = (payload.get('code') or '').strip()
    username = (payload.get('username') or '').strip()
    user = SystemUser.objects.filter(Q(code=code) | Q(username=username), active=True).first()
    if not user:
        messages.error(request, 'Compte LP Core non synchronisé dans System Manager.')
        return redirect('system_login')
    request.session['system_user_id'] = user.id
    messages.success(request, f'Connexion System Manager via LP Core : {user.first_name} {user.last_name}.')
    return redirect('system_dashboard')

def login_view(request):
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = SystemUser.objects.filter(username=username, active=True).first() or SystemUser.objects.filter(code=username, active=True).first()
        if user and user.check_password(password):
            request.session['system_user_id'] = user.id
            messages.success(request, f'Connexion System Manager : {user.full_name}.')
            return redirect('system_dashboard')
        messages.error(request, 'Identifiant ou mot de passe incorrect. Synchronisez depuis LP Core si nécessaire.')
    return render(request, 'system_manager/login.html')


def logout_view(request):
    request.session.pop('system_user_id', None)
    messages.success(request, 'Déconnexion System Manager effectuée.')
    return redirect('system_login')


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
            users_report = sync_users_from_lp_core(timeout=90, force_password=force_password, core_user_id=core_user_id)
            form_report = {'created': 0, 'updated': 0, 'errors': []}
            class_report = {'created': 0, 'updated': 0, 'errors': []}
            zone_report = {'zones_created': 0, 'zones_updated': 0, 'subzones_created': 0, 'subzones_updated': 0, 'errors': []}
            if not core_user_id:
                form_report = sync_formations_from_lp_core(timeout=90)
                class_report = sync_classes_from_lp_core(timeout=90)
                try:
                    zone_report = sync_workshop_zones_from_lp_core(timeout=90)
                except Exception as exc:
                    zone_report = {'errors': [str(exc)]}
                try:
                    block_report = sync_workshop_blocks_from_lp_core(timeout=90)
                except Exception as exc:
                    block_report = {'created': 0, 'updated': 0, 'slots_created': 0, 'slots_updated': 0, 'errors': [str(exc)]}
            else:
                block_report = {'created': 0, 'updated': 0, 'slots_created': 0, 'slots_updated': 0, 'errors': []}
            errors = users_report.get('errors', []) + form_report.get('errors', []) + class_report.get('errors', []) + zone_report.get('errors', []) + block_report.get('errors', [])
            return JsonResponse({'ok': len(errors) == 0, 'users': users_report, 'formations': form_report, 'classes': class_report, 'zones': zone_report, 'blocks': block_report, 'errors': errors})
        except Exception as exc:
            return JsonResponse({'ok': False, 'error': str(exc)}, status=500)
    user = current_system_user(request)
    if not user or not user.is_admin_like:
        messages.error(request, 'Synchronisation System Manager réservée aux administrateurs.')
        return redirect('system_login')
    try:
        users_report = sync_users_from_lp_core(timeout=90)
        form_report = sync_formations_from_lp_core(timeout=90)
        class_report = sync_classes_from_lp_core(timeout=90)
        try:
            zone_report = sync_workshop_zones_from_lp_core(timeout=90)
        except Exception as exc:
            zone_report = {'errors': [str(exc)]}
        try:
            block_report = sync_workshop_blocks_from_lp_core(timeout=90)
        except Exception as exc:
            block_report = {'created': 0, 'updated': 0, 'slots_created': 0, 'slots_updated': 0, 'errors': [str(exc)]}
        errors = users_report['errors'] + form_report['errors'] + class_report.get('errors', []) + zone_report.get('errors', []) + block_report.get('errors', [])
        if errors:
            messages.warning(request, f"Synchronisation partielle : {users_report['created']} utilisateurs créés, {users_report['updated']} mis à jour, {len(errors)} erreurs.")
        else:
            messages.success(request, f"Synchronisation terminée : {users_report['created']} utilisateurs créés, {users_report['updated']} mis à jour, {form_report['created']} formations créées, {class_report.get('created', 0)} classes créées, {zone_report.get('zones_created', 0)} zones créées, {block_report.get('created', 0)} blocs atelier créés.")
    except Exception as exc:
        messages.error(request, f'Échec synchronisation LP Core → System Manager : {exc}')
    return redirect('system_dashboard')


@system_login_required
def dashboard(request):
    today = timezone.localdate()
    start_day = timezone.make_aware(datetime.combine(today, time.min))
    end_day = timezone.make_aware(datetime.combine(today, time.max))
    open_sessions = WorkSession.objects.filter(statut='ouverte').select_related('systeme', 'utilisateur')[:8]
    context = {
        'systems_count': EducationalSystem.objects.filter(actif=True).count(),
        'available_count': EducationalSystem.objects.filter(actif=True, statut='disponible').count(),
        'maintenance_count': EducationalSystem.objects.filter(actif=True, statut__in=['maintenance', 'hors_service']).count(),
        'reservations_today_count': Reservation.objects.filter(date_debut__lte=end_day, date_fin__gte=start_day).exclude(statut__in=['annulee', 'refusee']).count(),
        'open_sessions_count': WorkSession.objects.filter(statut='ouverte').count(),
        'open_anomalies_count': SystemAnomaly.objects.exclude(statut__in=['resolue', 'annulee']).count(),
        'reservations_today': Reservation.objects.select_related('systeme', 'professeur', 'formation', 'niveau').filter(date_debut__lte=end_day, date_fin__gte=start_day).exclude(statut__in=['annulee', 'refusee']).order_by('date_debut')[:12],
        'open_sessions': open_sessions,
        'recent_anomalies': SystemAnomaly.objects.select_related('systeme', 'signalee_par').exclude(statut__in=['resolue', 'annulee']).order_by('-created_at')[:8],
        'zones_stats': EducationalSystem.objects.values('zone__nom').annotate(count=Count('id')).order_by('zone__nom'),
    }
    return render(request, 'system_manager/dashboard.html', context)


@system_login_required
def system_list(request):
    systems = EducationalSystem.objects.select_related('zone', 'sous_zone', 'professeur_referent').prefetch_related('formations', 'niveaux')
    q = (request.GET.get('q') or '').strip()
    zone = request.GET.get('zone') or ''
    formation = request.GET.get('formation') or ''
    statut = request.GET.get('statut') or ''
    if q:
        systems = systems.filter(Q(code__icontains=q) | Q(designation__icontains=q) | Q(description__icontains=q))
    if zone:
        systems = systems.filter(zone_id=zone)
    if formation:
        systems = systems.filter(formations__id=formation)
    if statut:
        systems = systems.filter(statut=statut)
    systems = systems.distinct()
    return render(request, 'system_manager/system_list.html', {
        'systems': systems[:500], 'q': q, 'zones': WorkshopZone.objects.filter(active=True), 'formations': Formation.objects.filter(active=True),
        'status_choices': EducationalSystem.STATUS_CHOICES, 'selected_zone': zone, 'selected_formation': formation, 'selected_statut': statut,
    })


@system_login_required
def system_detail(request, pk):
    systeme = get_object_or_404(EducationalSystem.objects.select_related('zone', 'sous_zone', 'professeur_referent').prefetch_related('formations', 'niveaux'), pk=pk)
    docs_by_category = []
    categories = DocumentCategory.objects.filter(active=True).order_by('ordre')
    for cat in categories:
        docs_by_category.append((cat, systeme.documents.filter(categorie=cat, actif=True)))
    uncategorized_docs = systeme.documents.filter(categorie__isnull=True, actif=True)
    current_reservation = current_reservation_for_system(systeme)
    context = {
        'systeme': systeme,
        'effective_status': system_effective_status(systeme),
        'docs_by_category': docs_by_category,
        'uncategorized_docs': uncategorized_docs,
        'check_items': systeme.check_items.filter(actif=True),
        'current_reservation': current_reservation,
        'upcoming_reservations': upcoming_reservations(systeme, 8),
        'open_sessions': systeme.sessions.filter(statut='ouverte').select_related('utilisateur'),
        'recent_sessions': systeme.sessions.select_related('utilisateur', 'formation', 'niveau', 'professeur_referent').order_by('-date_prise')[:10],
        'anomalies': systeme.anomalies.select_related('signalee_par').order_by('-created_at')[:10],
    }
    return render(request, 'system_manager/system_detail.html', context)


@system_edit_required
@require_http_methods(['GET', 'POST'])
def system_create(request):
    user = current_system_user(request)
    if not can_create_systems(user):
        messages.error(request, 'Tu n’as pas de droit actif pour créer un système.')
        return redirect('system_list')
    form = EducationalSystemForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        systeme = form.save()
        _ensure_default_check_items(systeme)
        messages.success(request, f'Système {systeme.code} créé.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer un système pédagogique'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def system_update(request, pk):
    systeme = get_object_or_404(EducationalSystem, pk=pk)
    user = current_system_user(request)
    if not can_edit_systems(user, systeme):
        messages.error(request, 'Tu n’as pas de droit actif pour modifier ce système.')
        return redirect('system_detail', systeme.pk)
    form = EducationalSystemForm(request.POST or None, request.FILES or None, instance=systeme)
    if request.method == 'POST' and form.is_valid():
        systeme = form.save()
        messages.success(request, f'Système {systeme.code} modifié.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier {systeme.code}'})


def _ensure_default_check_items(systeme):
    if systeme.check_items.exists():
        return
    templates = list(DefaultCheckTemplate.objects.filter(active=True).order_by('ordre', 'id'))
    if templates:
        for tpl in templates:
            tpl.create_for_system(systeme)
        return
    defaults = [
        ('Système propre et en ordre', 'deux', True, False, 'oui'),
        ('Zone autour du système dégagée', 'deux', True, False, 'oui'),
        ('Classeur présent', 'deux', True, False, 'oui'),
        ('Classeur complet', 'deux', True, False, 'oui'),
        ('Système allumé ou éteint selon consigne', 'deux', True, False, 'oui'),
        ('Aucun câble, flexible ou accessoire visiblement endommagé', 'deux', True, True, 'oui'),
        ('Équipements de sécurité présents si nécessaires', 'deux', True, True, 'oui'),
        ('Défaut ou anomalie constatée', 'deux', False, False, 'non'),
    ]
    for idx, (label, phase, obligatoire, bloquant, expected) in enumerate(defaults, start=1):
        CheckItem.objects.create(systeme=systeme, libelle=label, phase=phase, obligatoire=obligatoire, bloquant_si_non=bloquant, expected_response=expected, ordre=idx*10)


@system_admin_required
@require_http_methods(['GET', 'POST'])
def document_add(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = SystemDocumentForm(request.POST or None, request.FILES or None, systeme=systeme)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.systeme = systeme
        doc.ajoute_par = current_system_user(request)
        if doc.categorie and ('CORR' in doc.categorie.code.upper() or 'CORRECTION' in doc.categorie.nom.upper()):
            doc.teacher_only = True
            doc.visible_students = False
        try:
            doc.full_clean()
            doc.save()
            messages.success(request, 'Document ajouté.')
            return redirect('system_detail', systeme.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Ajouter un document — {systeme.code}'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def document_update(request, pk):
    doc = get_object_or_404(SystemDocument.objects.select_related('systeme'), pk=pk)
    form = SystemDocumentForm(request.POST or None, request.FILES or None, instance=doc, systeme=doc.systeme)
    if request.method == 'POST' and form.is_valid():
        try:
            doc = form.save(commit=False)
            if doc.categorie and ('CORR' in doc.categorie.code.upper() or 'CORRECTION' in doc.categorie.nom.upper()):
                doc.teacher_only = True
                doc.visible_students = False
            doc.save()
            form.save_m2m()
            messages.success(request, 'Document modifié.')
            return redirect('system_detail', doc.systeme.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier un document — {doc.systeme.code}'})



@system_admin_required
@require_http_methods(['GET', 'POST'])
def document_new_version(request, pk):
    old = get_object_or_404(SystemDocument.objects.select_related('systeme', 'categorie'), pk=pk)
    initial = {
        'categorie': old.categorie_id,
        'titre': old.titre,
        'type_document': old.type_document,
        'parent_document': old.pk,
        'url': old.url,
        'description': old.description,
        'visible_students': old.visible_students,
        'teacher_only': old.teacher_only,
        'actif': True,
    }
    form = SystemDocumentForm(request.POST or None, request.FILES or None, initial=initial, systeme=old.systeme)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.systeme = old.systeme
        doc.parent_document = old
        doc.ajoute_par = current_system_user(request)
        if doc.categorie and ('CORR' in doc.categorie.code.upper() or 'CORRECTION' in doc.categorie.nom.upper()):
            doc.teacher_only = True
            doc.visible_students = False
        try:
            doc.full_clean()
            doc.save()
            old.actif = False
            old.save(update_fields=['actif', 'updated_at'])
            SystemChangeLog.objects.create(
                systeme=old.systeme,
                type_changement='document',
                titre=f'Nouvelle version : {doc.titre}',
                description=f'Remplace le document #{old.pk}.',
                version_avant=old.version,
                version_apres=doc.version,
                effectue_par=current_system_user(request),
                date_effet=timezone.localdate(),
            )
            messages.success(request, 'Nouvelle version ajoutée. L’ancienne version est désactivée mais reste historisée.')
            return redirect('system_detail', old.systeme.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Nouvelle version — {old.titre}'})


@system_admin_required
@require_http_methods(['POST'])
def document_delete(request, pk):
    doc = get_object_or_404(SystemDocument.objects.select_related('systeme'), pk=pk)
    system_pk = doc.systeme.pk
    title = doc.titre
    doc.delete()
    messages.success(request, f'Document supprimé : {title}.')
    return redirect('system_detail', system_pk)


@system_edit_required
@require_http_methods(['GET', 'POST'])
def checkitem_add(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = CheckItemForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.systeme = systeme
        item.save()
        messages.success(request, 'Point de check ajouté.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Ajouter un point de check — {systeme.code}'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def checkitem_update(request, pk):
    item = get_object_or_404(CheckItem, pk=pk)
    form = CheckItemForm(request.POST or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Point de check modifié.')
        return redirect('system_detail', item.systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier un point de check — {item.systeme.code}'})


@system_login_required
def reservation_calendar(request):
    raw_date = request.GET.get('date')
    try:
        day = datetime.strptime(raw_date, '%Y-%m-%d').date() if raw_date else timezone.localdate()
    except ValueError:
        day = timezone.localdate()
    week_start, week_end = week_bounds(day)
    start_dt = timezone.make_aware(datetime.combine(week_start, time.min))
    end_dt = timezone.make_aware(datetime.combine(week_end, time.min))
    reservations = Reservation.objects.select_related('systeme', 'professeur', 'formation', 'niveau').filter(date_debut__lt=end_dt, date_fin__gt=start_dt).exclude(statut__in=['annulee', 'refusee']).order_by('date_debut')
    days = [week_start + timedelta(days=i) for i in range(5)]
    hours = list(range(8, 19))
    calendar = []
    for h in hours:
        row = []
        for d in days:
            slot_start = timezone.make_aware(datetime.combine(d, time(hour=h, minute=0)))
            slot_end = slot_start + timedelta(hours=1)
            events = [r for r in reservations if r.date_debut < slot_end and r.date_fin > slot_start]
            row.append(events)
        calendar.append((h, row))
    return render(request, 'system_manager/reservation_calendar.html', {
        'days': days, 'hours': hours, 'calendar': calendar, 'week_start': week_start, 'week_end': week_end - timedelta(days=1),
        'prev_date': (week_start - timedelta(days=7)).isoformat(), 'next_date': (week_start + timedelta(days=7)).isoformat(), 'today': timezone.localdate(),
    })


@system_login_required
def reservation_list(request):
    reservations = Reservation.objects.select_related('systeme', 'professeur', 'formation', 'niveau')
    q = (request.GET.get('q') or '').strip()
    if q:
        reservations = reservations.filter(Q(systeme__code__icontains=q) | Q(systeme__designation__icontains=q) | Q(classe_ou_groupe__icontains=q) | Q(tp_code__icontains=q) | Q(tp_titre__icontains=q))
    return render(request, 'system_manager/reservation_list.html', {'reservations': reservations.order_by('-date_debut')[:500], 'q': q})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def reservation_create(request):
    initial = {}
    system_id = request.GET.get('systeme')
    if system_id:
        initial['systeme'] = system_id
    user = current_system_user(request)
    if user and user.is_prof_like:
        initial['professeur'] = user.pk
    form = ReservationForm(request.POST or None, initial=initial)
    if request.method == 'POST' and form.is_valid():
        reservation = form.save(commit=False)
        try:
            reservation.full_clean()
            reservation.save()
            messages.success(request, 'Réservation créée.')
            return redirect('reservation_calendar')
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Réserver un système'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    form = ReservationForm(request.POST or None, instance=reservation)
    if request.method == 'POST' and form.is_valid():
        reservation = form.save(commit=False)
        try:
            reservation.full_clean()
            reservation.save()
            messages.success(request, 'Réservation modifiée.')
            return redirect('reservation_calendar')
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Modifier une réservation'})


@system_login_required
def system_qr_png(request, pk):
    systeme = get_object_or_404(EducationalSystem, pk=pk)
    url = settings.SYSTEM_MANAGER_PUBLIC_URL + reverse('worksession_start', args=[systeme.pk])
    img = qrcode.make(url)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


@system_login_required
@require_http_methods(['GET', 'POST'])
def worksession_start(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    user = current_system_user(request)
    open_existing = WorkSession.objects.filter(systeme=systeme, utilisateur=user, statut='ouverte').order_by('-date_prise').first()
    if open_existing:
        messages.info(request, 'Une prise de poste est déjà ouverte pour ce système : passe directement à la restitution.')
        return redirect('worksession_return', open_existing.pk)
    current_reservation = current_reservation_for_system(systeme)
    initial = {'reservation': current_reservation}
    if current_reservation:
        initial.update({
            'professeur_referent': current_reservation.professeur_id,
            'formation': current_reservation.formation_id,
            'niveau': current_reservation.niveau_id,
            'classe_ou_groupe': current_reservation.classe_ou_groupe,
            'tp_code': current_reservation.tp_code,
            'tp_titre': current_reservation.tp_titre,
        })
    else:
        initial.update({'professeur_referent': systeme.professeur_referent_id})
    form = WorkSessionStartForm(request.POST or None, initial=initial)
    # On limite les réservations proposées au système et à la période courante/proche.
    form.fields['reservation'].queryset = Reservation.objects.filter(systeme=systeme).exclude(statut__in=['annulee', 'refusee']).order_by('-date_debut')[:20]
    items = systeme.check_items.filter(actif=True).order_by('ordre')
    if request.method == 'POST' and form.is_valid():
        missing = _validate_check_post(request, items)
        if missing:
            for msg in missing:
                form.add_error(None, msg)
        else:
            session = form.save(commit=False)
            session.systeme = systeme
            session.utilisateur = user
            session.date_prise = timezone.now()
            session.statut = 'ouverte'
            session.save()
            _save_check_responses(request, session, items, 'prise')
            if session.reservation:
                session.reservation.statut = 'en_cours'
                session.reservation.save(update_fields=['statut', 'updated_at'])
            systeme.statut = 'en_utilisation'
            systeme.save(update_fields=['statut', 'updated_at'])
            messages.success(request, 'Prise de poste enregistrée.')
            return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/worksession_start.html', {'systeme': systeme, 'form': form, 'items': items, 'current_reservation': current_reservation})


@system_login_required
@require_http_methods(['GET', 'POST'])
def worksession_return(request, pk):
    session = get_object_or_404(WorkSession.objects.select_related('systeme', 'reservation'), pk=pk)
    systeme = session.systeme
    form = WorkSessionReturnForm(request.POST or None, instance=session)
    items = systeme.check_items.filter(actif=True).order_by('ordre')
    if request.method == 'POST' and form.is_valid():
        missing = _validate_check_post(request, items)
        if missing:
            for msg in missing:
                form.add_error(None, msg)
        else:
            session = form.save(commit=False)
            session.date_restitution = timezone.now()
            has_blocking_no = False
            has_any_no = False
            for item in items:
                value = request.POST.get(f'item_{item.id}_value') or ''
                if value == 'non':
                    has_any_no = True
                    if item.bloquant_si_non:
                        has_blocking_no = True
            session.statut = 'anomalie' if has_any_no else 'restituee'
            session.save()
            _save_check_responses(request, session, items, 'restitution')
            if session.reservation:
                session.reservation.statut = 'terminee' if session.statut == 'restituee' else 'non_restituee'
                session.reservation.save(update_fields=['statut', 'updated_at'])
            systeme.statut = 'hors_service' if has_blocking_no else ('alerte' if has_any_no else 'disponible')
            systeme.save(update_fields=['statut', 'updated_at'])
            if has_any_no:
                SystemAnomaly.objects.create(
                    systeme=systeme,
                    session=session,
                    signalee_par=current_system_user(request),
                    titre=f'Anomalie signalée lors de la restitution du {timezone.localtime(session.date_restitution):%d/%m/%Y %H:%M}',
                    description=session.commentaire_restitution or 'Un ou plusieurs points de contrôle ont été renseignés à Non.',
                    gravite='bloquante' if has_blocking_no else 'mineure',
                    statut='ouverte',
                )
            messages.success(request, 'Restitution de poste enregistrée.')
            return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/worksession_return.html', {'session': session, 'systeme': systeme, 'form': form, 'items': items})


def _validate_check_post(request, items):
    errors = []
    for item in items:
        if not item.obligatoire:
            continue
        if item.type_reponse == 'oui_non_nc' and not request.POST.get(f'item_{item.id}_value'):
            errors.append(f'Réponse obligatoire : {item.libelle}')
        if item.type_reponse in {'texte', 'nombre'} and not (request.POST.get(f'item_{item.id}_text') or '').strip():
            errors.append(f'Réponse obligatoire : {item.libelle}')
        if item.type_reponse == 'photo' and not request.FILES.get(f'item_{item.id}_photo'):
            errors.append(f'Photo obligatoire : {item.libelle}')
    return errors


def _save_check_responses(request, session, items, phase):
    for item in items:
        CheckResponse.objects.create(
            session=session,
            item=item,
            phase=phase,
            valeur=request.POST.get(f'item_{item.id}_value') or '',
            texte=request.POST.get(f'item_{item.id}_text') or '',
            photo=request.FILES.get(f'item_{item.id}_photo') if f'item_{item.id}_photo' in request.FILES else None,
        )


@system_login_required
def history(request):
    sessions = WorkSession.objects.select_related('systeme', 'utilisateur', 'professeur_referent', 'formation', 'niveau').order_by('-date_prise')[:500]
    return render(request, 'system_manager/history.html', {'sessions': sessions})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def anomaly_create(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = SystemAnomalyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        anomaly = form.save(commit=False)
        anomaly.systeme = systeme
        anomaly.signalee_par = current_system_user(request)
        anomaly.save()
        if anomaly.gravite == 'bloquante':
            systeme.statut = 'hors_service'
        else:
            systeme.statut = 'alerte'
        systeme.save(update_fields=['statut', 'updated_at'])
        messages.success(request, 'Anomalie créée.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Signaler une anomalie — {systeme.code}'})


@system_admin_required
def referentials(request):
    return render(request, 'system_manager/referentials.html', {
        'zones': WorkshopZone.objects.all(),
        'subzones': WorkshopSubZone.objects.select_related('zone').all(),
        'formations': Formation.objects.all(),
        'niveaux': Niveau.objects.all(),
        'categories': DocumentCategory.objects.all(),
    })


@system_admin_required
@require_http_methods(['GET', 'POST'])
def zone_create(request):
    form = ZoneForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Zone créée.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer une zone atelier'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def subzone_create(request):
    form = SubZoneForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Sous-zone créée.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer une sous-zone atelier'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def niveau_create(request):
    form = NiveauForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Niveau créé.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer un niveau'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def doc_category_create(request):
    form = DocumentCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Rubrique documentaire créée.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer une rubrique documentaire'})


@system_login_required
def api_calendar_events(request):
    reservations = Reservation.objects.select_related('systeme', 'professeur').exclude(statut__in=['annulee', 'refusee']).order_by('date_debut')[:1000]
    return JsonResponse({'results': [{
        'id': r.id,
        'title': f'{r.systeme.code} — {r.classe_ou_groupe or r.professeur or "Réservation"}',
        'start': r.date_debut.isoformat(),
        'end': r.date_fin.isoformat(),
        'systeme': r.systeme.designation,
        'professeur': r.professeur.full_name if r.professeur else '',
        'statut': r.statut,
    } for r in reservations]})


def api_allowed(request):
    token = request.headers.get('X-API-Key') or request.GET.get('token')
    expected = getattr(settings, 'LP_CORE_API_TOKEN', '')
    if expected and token != expected:
        return False
    return True


def api_systems(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    systems = EducationalSystem.objects.select_related('zone').filter(actif=True).order_by('zone__code', 'code')
    return JsonResponse({'results': [{
        'id': s.id,
        'code': s.code,
        'designation': s.designation,
        'zone_code': s.zone.code if s.zone else '',
        'zone_nom': s.zone.nom if s.zone else '',
        'statut': system_effective_status(s),
        'actif': s.actif,
    } for s in systems]})


# --- Administration SQL base module ---
def sql_database_admin(request):
    from .permissions import system_admin_required
    from .db_sql_admin import render_sql_admin
    @system_admin_required
    def _view(req):
        return render_sql_admin(req, 'system_manager/sql_database.html', 'System Manager')
    return _view(request)


def sql_database_export(request):
    from .permissions import system_admin_required
    from .db_sql_admin import export_sql_response
    @system_admin_required
    def _view(req):
        return export_sql_response(req, 'system-manager')
    return _view(request)


def sql_database_import(request):
    from .permissions import system_admin_required
    from .db_sql_admin import import_sql_response
    @system_admin_required
    def _view(req):
        return import_sql_response(req, 'system_manager/sql_database.html', 'System Manager', 'system-manager')
    return _view(request)

def help_view(request):
    return render(request, 'system_manager/help.html')


def about_view(request):
    return render(request, 'system_manager/about.html')


# ---------------------------------------------------------------------------
# V0.3.3 — System Manager : classeur avancé, GMAO, blocs atelier
# ---------------------------------------------------------------------------

def _root_document_sections():
    roots = list(DocumentCategory.objects.filter(active=True, parent__isnull=True).order_by('section_code', 'ordre', 'code'))
    if roots:
        return roots
    # Fallback si la migration seed n'a pas encore créé les rubriques.
    return list(DocumentCategory.objects.filter(active=True).order_by('ordre', 'code'))


@system_login_required
def system_detail(request, pk):
    systeme = get_object_or_404(EducationalSystem.objects.select_related('zone', 'sous_zone', 'professeur_referent').prefetch_related('formations', 'niveaux'), pk=pk)
    docs_sections = []
    user = current_system_user(request)
    visible_doc_filter = Q(actif=True)
    if not (user and user.is_prof_like):
        visible_doc_filter &= Q(visible_students=True, teacher_only=False)
    for root in _root_document_sections():
        children = list(root.sous_categories.filter(active=True).order_by('ordre', 'code')) if hasattr(root, 'sous_categories') else []
        if not children:
            children = [root]
        child_rows = []
        for cat in children:
            child_rows.append((cat, systeme.documents.filter(visible_doc_filter, categorie=cat).select_related('parent_document').prefetch_related('versions').order_by('titre')))
        # documents posés directement sur le conteneur racine
        root_docs = systeme.documents.filter(visible_doc_filter, categorie=root).select_related('parent_document').prefetch_related('versions').order_by('titre') if children and children[0] != root else []
        docs_sections.append((root, child_rows, root_docs))
    context = {
        'systeme': systeme,
        'effective_status': system_effective_status(systeme),
        'docs_sections': docs_sections,
        'uncategorized_docs': systeme.documents.filter(visible_doc_filter, categorie__isnull=True).select_related('parent_document').prefetch_related('versions'),
        'check_items': systeme.check_items.filter(actif=True),
        'my_open_sessions': systeme.sessions.filter(statut='ouverte', utilisateur=user).select_related('utilisateur') if user else [],
        'can_edit_this_system': can_edit_systems(user, systeme),
        'current_reservation': current_reservation_for_system(systeme),
        'upcoming_reservations': upcoming_reservations(systeme, 8),
        'open_sessions': systeme.sessions.filter(statut='ouverte').select_related('utilisateur'),
        'recent_sessions': systeme.sessions.select_related('utilisateur', 'formation', 'niveau', 'professeur_referent').order_by('-date_prise')[:10],
        'anomalies': systeme.anomalies.select_related('signalee_par').order_by('-created_at')[:10],
        'tp_associations': systeme.tp_associations.filter(active=True).select_related('formation', 'niveau')[:50],
        'safety_links': systeme.safety_links.filter(active=True)[:50],
        'maintenance_interventions': systeme.maintenance_interventions.select_related('intervention_par').order_by('-created_at')[:12],
        'change_logs': systeme.change_logs.select_related('effectue_par').order_by('-date_effet', '-created_at')[:12],
    }
    return render(request, 'system_manager/system_detail.html', context)


@system_edit_required
@require_http_methods(['GET', 'POST'])
def tp_association_add(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = SystemTPAssociationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.systeme = systeme
        obj.save()
        messages.success(request, 'TP/TD associé au système.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Associer un TP/TD — {systeme.code}'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def safety_link_add(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = SystemSafetyLinkForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.systeme = systeme
        obj.save()
        messages.success(request, 'Lien sécurité ajouté au système.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Ajouter sécurité / risque / consignation — {systeme.code}'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def change_log_add(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = SystemChangeLogForm(request.POST or None, systeme=systeme)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        source_ref = form.cleaned_data.get('source_ref') or ''
        if source_ref.startswith('doc:'):
            doc = systeme.documents.filter(pk=source_ref.split(':', 1)[1]).first()
            if doc:
                obj.type_changement = 'document'
                obj.titre = obj.titre or f'Document : {doc.titre}'
                obj.description = obj.description or doc.description
                obj.version_avant = obj.version_avant or (doc.parent_document.version if doc.parent_document else '')
                obj.version_apres = obj.version_apres or doc.version
        elif source_ref.startswith('maint:'):
            maint = systeme.maintenance_interventions.filter(pk=source_ref.split(':', 1)[1]).first()
            if maint:
                obj.type_changement = 'maintenance'
                obj.titre = obj.titre or f'Intervention : {maint.reference}'
                obj.description = obj.description or (maint.conclusion_conformite or maint.action_realisee or maint.suite_a_donner)
        obj.systeme = systeme
        obj.effectue_par = current_system_user(request)
        obj.save()
        messages.success(request, 'Modification ajoutée à l’historique.')
        return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Historiser une modification — {systeme.code}'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def maintenance_create(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = MaintenanceInterventionForm(request.POST or None)
    form.fields['safety_link'].queryset = systeme.safety_links.filter(active=True)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.systeme = systeme
        obj.intervention_par = current_system_user(request)
        obj.save()
        messages.success(request, 'Intervention maintenance / GMAO créée.')
        return redirect('maintenance_detail', obj.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Créer intervention maintenance — {systeme.code}'})


@system_login_required
def maintenance_detail(request, pk):
    intervention = get_object_or_404(MaintenanceIntervention.objects.select_related('systeme', 'intervention_par', 'safety_link'), pk=pk)
    return render(request, 'system_manager/maintenance_detail.html', {'intervention': intervention, 'systeme': intervention.systeme})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def maintenance_update(request, pk):
    intervention = get_object_or_404(MaintenanceIntervention.objects.select_related('systeme'), pk=pk)
    form = MaintenanceInterventionForm(request.POST or None, instance=intervention)
    form.fields['safety_link'].queryset = intervention.systeme.safety_links.filter(active=True)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Intervention mise à jour.')
        return redirect('maintenance_detail', intervention.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier intervention — {intervention.reference}'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def maintenance_checkline_add(request, intervention_pk):
    intervention = get_object_or_404(MaintenanceIntervention, pk=intervention_pk)
    form = MaintenanceCheckLineForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.intervention = intervention
        obj.save()
        messages.success(request, 'Ligne de contrôle ajoutée.')
        return redirect('maintenance_detail', intervention.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Ajouter contrôle — {intervention.reference}'})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def maintenance_drawing_add(request, intervention_pk):
    intervention = get_object_or_404(MaintenanceIntervention, pk=intervention_pk)
    form = MaintenanceDrawingZoneForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save(commit=False)
        obj.intervention = intervention
        obj.save()
        messages.success(request, 'Zone photo/dessin ajoutée.')
        return redirect('maintenance_detail', intervention.pk)
    return render(request, 'system_manager/drawing_form.html', {'form': form, 'title': f'Zone photo/dessin — {intervention.reference}'})


@system_login_required
def reservation_list(request):
    reservations = Reservation.objects.select_related('systeme', 'systeme__zone', 'professeur', 'formation', 'niveau')
    q = (request.GET.get('q') or '').strip()
    zone = request.GET.get('zone') or ''
    formation = request.GET.get('formation') or ''
    niveau = request.GET.get('niveau') or ''
    classe = request.GET.get('classe') or ''
    statut = request.GET.get('statut') or ''
    if q:
        reservations = reservations.filter(Q(systeme__code__icontains=q) | Q(systeme__designation__icontains=q) | Q(classe_ou_groupe__icontains=q) | Q(tp_code__icontains=q) | Q(tp_titre__icontains=q) | Q(sequence_title__icontains=q))
    if zone:
        reservations = reservations.filter(systeme__zone_id=zone)
    if formation:
        reservations = reservations.filter(formation_id=formation)
    if niveau:
        reservations = reservations.filter(niveau_id=niveau)
    if classe:
        reservations = reservations.filter(classe_ou_groupe__icontains=classe)
    if statut:
        reservations = reservations.filter(statut=statut)
    return render(request, 'system_manager/reservation_list.html', {
        'reservations': reservations.order_by('-date_debut')[:500], 'q': q, 'selected_zone': zone, 'selected_formation': formation, 'selected_niveau': niveau,
        'selected_classe': classe, 'selected_statut': statut, 'zones': WorkshopZone.objects.filter(active=True), 'formations': Formation.objects.filter(active=True),
        'niveaux': Niveau.objects.filter(active=True), 'status_choices': Reservation.STATUS_CHOICES,
    })


@system_edit_required
@require_http_methods(['GET', 'POST'])
def reservation_block_create(request):
    form = ReservationGroupForm, SystemSearchForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        start_date = data['date_debut']
        end_date = data['date_fin']
        if start_date > end_date:
            form.add_error('date_fin', 'La fin de période doit être postérieure au début.')
        slots = list(data['slots'])
        block = data.get('block')
        if block and not slots:
            slots = list(block.slots.filter(active=True))
        if not slots:
            form.add_error('slots', 'Sélectionner au moins une demi-journée / un créneau.')
        if not form.errors:
            created = 0
            skipped = 0
            errors = []
            current = start_date
            while current <= end_date:
                for slot in slots:
                    if current.weekday() != slot.day_of_week:
                        continue
                    slot_start = timezone.make_aware(datetime.combine(current, slot.start_time))
                    slot_end = timezone.make_aware(datetime.combine(current, slot.end_time))
                    for systeme in data['systemes']:
                        reservation = Reservation(
                            systeme=systeme, professeur=data.get('professeur'), formation=data.get('formation'), niveau=data.get('niveau'),
                            classe_ou_groupe=data.get('classe_ou_groupe') or '', tp_code=data.get('sequence_code') or '', tp_titre=data.get('sequence_title') or '',
                            reservation_mode='bloc_atelier', block_code=slot.block.code, block_name=slot.block.nom, slot_label=slot.label or str(slot),
                            sequence_code=data.get('sequence_code') or '', sequence_title=data.get('sequence_title') or '',
                            date_debut=slot_start, date_fin=slot_end, commentaire=data.get('commentaire') or '', statut='confirmee'
                        )
                        try:
                            reservation.full_clean()
                            reservation.save()
                            created += 1
                        except ValidationError as exc:
                            skipped += 1
                            errors.append(f'{systeme.code} {slot_start:%d/%m %H:%M}: {exc.messages[0] if hasattr(exc, "messages") else exc}')
                current += timedelta(days=1)
            if created:
                messages.success(request, f'{created} réservation(s) créée(s) par bloc atelier.')
            if skipped:
                messages.warning(request, f'{skipped} créneau(x) ignoré(s) pour conflit ou erreur. Exemple : {errors[0] if errors else "voir logs"}')
            return redirect('reservation_list')
    return render(request, 'system_manager/reservation_block_form.html', {'form': form, 'title': 'Réserver par bloc atelier / séquence'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def workshop_block_create(request):
    form = WorkshopBlockForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        obj = form.save()
        messages.success(request, 'Bloc atelier créé dans System Manager.')
        return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer un bloc atelier'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def workshop_block_slot_create(request):
    form = WorkshopBlockSlotForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Créneau de bloc atelier créé.')
        return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer une demi-journée / créneau de bloc'})



@system_admin_required
@require_http_methods(['GET', 'POST'])
def zone_update(request, pk):
    obj = get_object_or_404(WorkshopZone, pk=pk)
    form = ZoneForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Zone modifiée.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier zone — {obj.code}'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def subzone_update(request, pk):
    obj = get_object_or_404(WorkshopSubZone, pk=pk)
    form = SubZoneForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Sous-zone modifiée.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier sous-zone — {obj.code}'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def niveau_update(request, pk):
    obj = get_object_or_404(Niveau, pk=pk)
    form = NiveauForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Niveau modifié.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier niveau — {obj.code}'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def doc_category_update(request, pk):
    obj = get_object_or_404(DocumentCategory, pk=pk)
    form = DocumentCategoryForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Rubrique documentaire modifiée.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier rubrique — {obj.code}'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def workshop_block_update(request, pk):
    obj = get_object_or_404(WorkshopBlock, pk=pk)
    form = WorkshopBlockForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Bloc atelier modifié.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier bloc atelier — {obj.code}'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def workshop_block_slot_update(request, pk):
    obj = get_object_or_404(WorkshopBlockSlot, pk=pk)
    form = WorkshopBlockSlotForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save(); messages.success(request, 'Créneau de bloc modifié.'); return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Modifier créneau — {obj.block.code}'})


@system_admin_required
def system_backup(request):
    if request.method == 'POST' and request.POST.get('action') == 'download_backup':
        buffer = BytesIO()
        db_name = settings.DATABASES['default']['NAME']
        with zipfile.ZipFile(buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
            if db_name and Path(db_name).exists():
                zf.write(db_name, arcname='system-manager.sqlite3')
            zf.writestr('manifest.txt', f'System Manager backup\ncreated={timezone.now().isoformat()}\n')
        buffer.seek(0)
        filename = f'system-manager-backup-{timezone.now():%Y%m%d-%H%M%S}.zip'
        response = HttpResponse(buffer.getvalue(), content_type='application/zip')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
    return render(request, 'system_manager/backup.html')


@csrf_exempt
@require_http_methods(['POST'])
def api_sync_blocks(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    try:
        report = sync_workshop_blocks_from_lp_core(timeout=90)
        return JsonResponse({'ok': len(report.get('errors', [])) == 0, 'report': report})
    except Exception as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)


@system_admin_required
def referentials(request):
    return render(request, 'system_manager/referentials.html', {
        'zones': WorkshopZone.objects.all(),
        'subzones': WorkshopSubZone.objects.select_related('zone').all(),
        'formations': Formation.objects.all(),
        'niveaux': Niveau.objects.all(),
        'categories': DocumentCategory.objects.select_related('parent').all(),
        'blocks': WorkshopBlock.objects.prefetch_related('formations', 'niveaux', 'slots').all(),
    })


# ---------------------------------------------------------------------------
# V0.3.4 — corrections ergonomie System Manager : classeur propre, réservations par dossier, administration référentiels
# ---------------------------------------------------------------------------
CANONICAL_DOC_ROOT_CODES = ['01_PRESENTATION', '02_PLANS_SCHEMAS_CALCULS', '03_DOCUMENTATIONS_TECHNIQUES', '04_PROGRAMMES', '05_TP_TD_ASSOCIES', '06_SECURITE_RISQUES_CONSIGNATION', '07_MAINTENANCE_DEPANNAGE', '08_HISTORIQUE_MODIFICATIONS']


def _root_document_sections():
    roots = list(DocumentCategory.objects.filter(active=True, parent__isnull=True, code__in=CANONICAL_DOC_ROOT_CODES).order_by('section_code', 'ordre', 'code'))
    # ordre strict 01→08, même si SQLite trie autrement
    return sorted(roots, key=lambda c: CANONICAL_DOC_ROOT_CODES.index(c.code) if c.code in CANONICAL_DOC_ROOT_CODES else 999)


def _candidate_systems(request):
    qs = EducationalSystem.objects.select_related('zone', 'sous_zone').filter(actif=True)
    q = (request.GET.get('q') or '').strip()
    zone = request.GET.get('zone') or ''
    subzone = request.GET.get('sous_zone') or ''
    statut = request.GET.get('statut') or ''
    if q:
        qs = qs.filter(Q(code__icontains=q) | Q(designation__icontains=q) | Q(description__icontains=q))
    if zone:
        qs = qs.filter(zone_id=zone)
    if subzone:
        qs = qs.filter(sous_zone_id=subzone)
    if statut:
        qs = qs.filter(statut=statut)
    return qs.order_by('zone__code', 'sous_zone__code', 'code')


def _create_one_reservation(group, systeme, start_dt, end_dt, slot_label=''):
    formation = group.classe.formation if group.classe and group.classe.formation else None
    reservation = Reservation(
        group=group,
        systeme=systeme,
        professeur=group.professeur,
        formation=formation,
        classe_ou_groupe=group.classe_ou_groupe,
        tp_code=group.tp_code,
        tp_titre=group.tp_titre,
        reservation_mode=group.reservation_mode,
        block_code=group.block.code if group.block else '',
        block_name=group.block.nom if group.block else '',
        slot_label=slot_label,
        sequence_code=group.sequence_code,
        sequence_title=group.sequence_title,
        date_debut=start_dt,
        date_fin=end_dt,
        statut='confirmee' if group.statut == 'confirmee' else 'brouillon',
        commentaire=group.commentaire,
    )
    reservation.full_clean()
    reservation.save()
    return reservation


def _add_systems_to_group(group, systems):
    created = 0
    skipped = []
    if group.reservation_mode == 'bloc_atelier' and group.slots.exists():
        start_day = timezone.localtime(group.date_debut).date()
        end_day = timezone.localtime(group.date_fin).date()
        current = start_day
        slots = list(group.slots.select_related('block').filter(active=True))
        while current <= end_day:
            for slot in slots:
                if current.weekday() != slot.day_of_week:
                    continue
                start_dt = timezone.make_aware(datetime.combine(current, slot.start_time))
                end_dt = timezone.make_aware(datetime.combine(current, slot.end_time))
                for systeme in systems:
                    try:
                        _create_one_reservation(group, systeme, start_dt, end_dt, slot.label or slot.get_day_of_week_display())
                        created += 1
                    except ValidationError as exc:
                        skipped.append(f'{systeme.code} {current:%d/%m} {slot.start_time:%H:%M}-{slot.end_time:%H:%M} : {exc.messages[0] if hasattr(exc, "messages") else exc}')
            current += timedelta(days=1)
    else:
        for systeme in systems:
            try:
                _create_one_reservation(group, systeme, group.date_debut, group.date_fin)
                created += 1
            except ValidationError as exc:
                skipped.append(f'{systeme.code} : {exc.messages[0] if hasattr(exc, "messages") else exc}')
    return created, skipped


@system_login_required
def reservation_calendar(request):
    raw_date = request.GET.get('date')
    try:
        day = datetime.strptime(raw_date, '%Y-%m-%d').date() if raw_date else timezone.localdate()
    except ValueError:
        day = timezone.localdate()
    week_start, week_end = week_bounds(day)
    start_dt = timezone.make_aware(datetime.combine(week_start, time.min))
    end_dt = timezone.make_aware(datetime.combine(week_end, time.min))
    zone_id = request.GET.get('zone') or ''
    subzone_id = request.GET.get('sous_zone') or ''
    reservations = Reservation.objects.select_related('group', 'systeme', 'systeme__zone', 'systeme__sous_zone', 'professeur', 'formation', 'niveau').filter(date_debut__lt=end_dt, date_fin__gt=start_dt).exclude(statut__in=['annulee', 'refusee']).order_by('date_debut')
    if zone_id:
        reservations = reservations.filter(systeme__zone_id=zone_id)
    if subzone_id:
        reservations = reservations.filter(systeme__sous_zone_id=subzone_id)
    reservations = list(reservations)
    days = [week_start + timedelta(days=i) for i in range(5)]
    hours = list(range(8, 19))
    calendar = []
    for h in hours:
        row = []
        for d in days:
            slot_start = timezone.make_aware(datetime.combine(d, time(hour=h, minute=0)))
            slot_end = slot_start + timedelta(hours=1)
            events = [r for r in reservations if r.date_debut < slot_end and r.date_fin > slot_start]
            row.append(events)
        calendar.append((h, row))
    filter_suffix = ''
    if zone_id:
        filter_suffix += f'&zone={zone_id}'
    if subzone_id:
        filter_suffix += f'&sous_zone={subzone_id}'
    return render(request, 'system_manager/reservation_calendar.html', {
        'days': days, 'hours': hours, 'calendar': calendar, 'week_start': week_start, 'week_end': week_end - timedelta(days=1),
        'prev_date': (week_start - timedelta(days=7)).isoformat(), 'next_date': (week_start + timedelta(days=7)).isoformat(), 'today': timezone.localdate(),
        'zones': WorkshopZone.objects.filter(active=True).order_by('ordre_affichage', 'code'),
        'subzones': WorkshopSubZone.objects.filter(active=True).select_related('zone').order_by('zone__code', 'ordre_affichage', 'code'),
        'selected_zone': zone_id,
        'selected_subzone': subzone_id,
        'filter_suffix': filter_suffix,
    })


@system_login_required
def reservation_list(request):
    q = (request.GET.get('q') or '').strip()
    groups = ReservationGroup.objects.select_related('professeur', 'classe', 'block').prefetch_related('reservations')
    if q:
        groups = groups.filter(Q(titre__icontains=q) | Q(classe_ou_groupe__icontains=q) | Q(sequence_title__icontains=q) | Q(tp_titre__icontains=q) | Q(block__nom__icontains=q))
    return render(request, 'system_manager/reservation_list.html', {'groups': groups.order_by('-date_debut')[:300], 'q': q})


@system_edit_required
@require_http_methods(['GET', 'POST'])
def reservation_create(request):
    initial = {}
    mode = request.GET.get('mode') or request.GET.get('reservation_mode')
    if mode in {'ponctuelle', 'bloc_atelier', 'sequence_tp'}:
        initial['reservation_mode'] = mode
    user = current_system_user(request)
    if user and user.is_prof_like:
        initial['professeur'] = user.pk
    initial_system_id = request.GET.get('systeme') or ''
    form = ReservationGroupForm(request.POST or None, initial=initial)
    sequences = SystemTPAssociation.objects.filter(active=True).exclude(sequence_titre='').order_by('sequence_titre').values_list('sequence_code', 'sequence_titre').distinct()[:300]
    if request.method == 'POST' and form.is_valid():
        group = form.save(commit=False)
        try:
            group.full_clean()
            group.save()
            form.save_m2m()
            if initial_system_id:
                systeme = EducationalSystem.objects.filter(pk=initial_system_id, actif=True).first()
                if systeme:
                    created, skipped = _add_systems_to_group(group, [systeme])
                    if skipped:
                        messages.warning(request, 'Réservation créée, mais le système initial est en conflit.')
            messages.success(request, 'Dossier de réservation créé. Ajoute maintenant les systèmes depuis l’interface de recherche.')
            return redirect('reservation_group_detail', group.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/reservation_group_form.html', {'form': form, 'title': 'Créer une réservation', 'sequences': sequences, 'initial_system_id': initial_system_id})


@system_edit_required
def reservation_block_create(request):
    return redirect(f"{reverse('reservation_create')}?mode=bloc_atelier")


@system_edit_required
@require_http_methods(['GET', 'POST'])
def reservation_group_detail(request, pk):
    group = get_object_or_404(ReservationGroup.objects.select_related('professeur', 'classe', 'block').prefetch_related('slots'), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('form_action') or ''
        if action == 'add_systems':
            systems = EducationalSystem.objects.filter(pk__in=request.POST.getlist('system_ids'), actif=True)
            created, skipped = _add_systems_to_group(group, systems)
            if created:
                messages.success(request, f'{created} réservation(s) système créée(s).')
            if skipped:
                messages.warning(request, 'Conflits ignorés : ' + ' | '.join(skipped[:6]))
            return redirect('reservation_group_detail', group.pk)
        if action == 'delete_reservations':
            count = group.reservations.filter(pk__in=request.POST.getlist('reservation_ids')).delete()[0]
            messages.success(request, f'{count} ligne(s) supprimée(s).')
            return redirect('reservation_group_detail', group.pk)
        if action == 'confirm_group':
            group.statut = 'confirmee'; group.save(update_fields=['statut', 'updated_at'])
            group.reservations.exclude(statut__in=['annulee', 'refusee']).update(statut='confirmee')
            messages.success(request, 'Dossier confirmé.')
            return redirect('reservation_group_detail', group.pk)
    candidates = _candidate_systems(request)[:120]
    selected_system_ids = set(group.reservations.values_list('systeme_id', flat=True))
    return render(request, 'system_manager/reservation_group_detail.html', {
        'group': group,
        'reservations': group.reservations.select_related('systeme', 'professeur').order_by('date_debut', 'systeme__code'),
        'candidates': candidates,
        'selected_system_ids': selected_system_ids,
        'zones': WorkshopZone.objects.filter(active=True).order_by('ordre_affichage', 'code'),
        'subzones': WorkshopSubZone.objects.filter(active=True).select_related('zone').order_by('zone__code', 'ordre_affichage', 'code'),
        'status_choices': EducationalSystem.STATUS_CHOICES,
        'q': request.GET.get('q', ''),
        'selected_zone': request.GET.get('zone', ''),
        'selected_subzone': request.GET.get('sous_zone', ''),
        'selected_statut': request.GET.get('statut', ''),
    })


@system_edit_required
@require_http_methods(['GET', 'POST'])
def reservation_update(request, pk):
    reservation = get_object_or_404(Reservation, pk=pk)
    # L'ancienne page par ligne reste accessible pour correction ponctuelle, mais les créations passent par le dossier.
    form = ReservationForm(request.POST or None, instance=reservation)
    if request.method == 'POST' and form.is_valid():
        reservation = form.save(commit=False)
        try:
            reservation.full_clean()
            reservation.save()
            messages.success(request, 'Ligne de réservation modifiée.')
            return redirect('reservation_group_detail', reservation.group_id) if reservation.group_id else redirect('reservation_calendar')
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Modifier une ligne de réservation'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def referentials(request):
    if request.method == 'POST':
        action = request.POST.get('form_action') or ''
        model_map = {
            'delete_zones': (WorkshopZone, 'selected_zones'),
            'delete_subzones': (WorkshopSubZone, 'selected_subzones'),
            'delete_classes': (SchoolClass, 'selected_classes'),
            'delete_niveaux': (Niveau, 'selected_niveaux'),
            'delete_categories': (DocumentCategory, 'selected_categories'),
            'delete_blocks': (WorkshopBlock, 'selected_blocks'),
            'delete_slots': (WorkshopBlockSlot, 'selected_slots'),
            'delete_default_checks': (DefaultCheckTemplate, 'selected_default_checks'),
        }
        if action == 'sync_core_to_system':
            try:
                sync_formations_from_lp_core(timeout=90)
                sync_classes_from_lp_core(timeout=90)
                sync_workshop_zones_from_lp_core(timeout=90)
                sync_workshop_blocks_from_lp_core(timeout=90)
                messages.success(request, 'Synchronisation LP Core → System Manager effectuée.')
            except Exception as exc:
                messages.error(request, f'Synchronisation LP Core → System Manager impossible : {exc}')
            return redirect('system_referentials')
        if action == 'sync_system_to_core':
            try:
                report = push_workshop_referentials_to_lp_core(timeout=90)
                messages.success(request, f'Synchronisation System Manager → LP Core demandée : {report}')
            except Exception as exc:
                messages.error(request, f'Synchronisation System Manager → LP Core impossible : {exc}')
            return redirect('system_referentials')
        if action in model_map:
            model, field = model_map[action]
            ids = request.POST.getlist(field)
            try:
                count = model.objects.filter(pk__in=ids).delete()[0]
                messages.success(request, f'{count} objet(s) supprimé(s).')
            except Exception as exc:
                messages.error(request, f'Suppression impossible : {exc}')
            return redirect('system_referentials')
    return render(request, 'system_manager/referentials.html', {
        'zones': WorkshopZone.objects.prefetch_related('sous_zones').all(),
        'subzones': WorkshopSubZone.objects.select_related('zone').all(),
        'formations': Formation.objects.all(),
        'classes': SchoolClass.objects.select_related('formation').all().order_by('nom', 'school_year'),
        'niveaux': Niveau.objects.all(),
        'categories': DocumentCategory.objects.select_related('parent').all(),
        'blocks': WorkshopBlock.objects.prefetch_related('classes', 'slots').all(),
        'slots': WorkshopBlockSlot.objects.select_related('block').all(),
        'default_checks': DefaultCheckTemplate.objects.all().order_by('ordre', 'id'),
    })




@system_admin_required
@require_http_methods(['GET', 'POST'])
def temporary_permissions(request):
    edit_id = request.GET.get('edit') or ''
    instance = TemporarySystemPermission.objects.filter(pk=edit_id).first() if edit_id else None
    if request.method == 'POST':
        action = request.POST.get('form_action') or ''
        if action == 'delete_permissions':
            count = TemporarySystemPermission.objects.filter(pk__in=request.POST.getlist('selected_permissions')).delete()[0]
            messages.success(request, f'{count} droit(s) temporaire(s) supprimé(s).')
            return redirect('system_temporary_permissions')
        instance = TemporarySystemPermission.objects.filter(pk=request.POST.get('permission_id')).first() if request.POST.get('permission_id') else None
        form = TemporarySystemPermissionForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.granted_by = current_system_user(request)
            obj.save()
            form.save_m2m()
            messages.success(request, 'Droit temporaire enregistré.')
            return redirect('system_temporary_permissions')
    else:
        form = TemporarySystemPermissionForm(instance=instance)
    return render(request, 'system_manager/temporary_permissions.html', {
        'form': form,
        'edit_permission': instance,
        'permissions': TemporarySystemPermission.objects.select_related('user', 'granted_by').prefetch_related('zones', 'systems').order_by('-date_debut')[:500],
        'now': timezone.now(),
    })


@system_login_required
def api_systems(request):
    systems = _candidate_systems(request)[:150]
    return JsonResponse({'results': [{
        'id': s.id,
        'code': s.code,
        'designation': s.designation,
        'zone_code': s.zone.code if s.zone else '',
        'zone_nom': s.zone.nom if s.zone else '',
        'sous_zone_code': s.sous_zone.code if s.sous_zone else '',
        'sous_zone_nom': s.sous_zone.nom if s.sous_zone else '',
        'statut': system_effective_status(s),
        'actif': s.actif,
    } for s in systems]})

# ---------------------------------------------------------------------------
# V0.3.7 — prévisualisation Office, checks attendus, anomalies, affichage dynamique
# ---------------------------------------------------------------------------
import os
import shutil
import subprocess
import tempfile
from django.core.files import File
from django.views.decorators.clickjacking import xframe_options_sameorigin

OFFICE_PREVIEW_EXTENSIONS = {'.doc', '.docx', '.odt', '.rtf', '.xls', '.xlsx', '.ods', '.ppt', '.pptx', '.odp'}


def _is_office_preview_candidate(doc):
    if not doc or not doc.fichier:
        return False
    return Path(doc.fichier.name).suffix.lower() in OFFICE_PREVIEW_EXTENSIONS


def _generate_document_preview(doc):
    """Convertit un document Office en PDF via LibreOffice headless si disponible."""
    if not _is_office_preview_candidate(doc):
        doc.preview_status = 'unsupported'
        doc.preview_error = ''
        doc.save(update_fields=['preview_status', 'preview_error', 'updated_at'])
        return False
    if not shutil.which('libreoffice'):
        doc.preview_status = 'error'
        doc.preview_error = 'LibreOffice indisponible dans le conteneur.'
        doc.save(update_fields=['preview_status', 'preview_error', 'updated_at'])
        return False
    try:
        src = Path(doc.fichier.path)
        with tempfile.TemporaryDirectory() as tmp:
            cmd = ['libreoffice', '--headless', '--nologo', '--nofirststartwizard', '--convert-to', 'pdf', '--outdir', tmp, str(src)]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=90)
            if result.returncode != 0:
                raise RuntimeError((result.stderr or result.stdout or 'Conversion impossible').strip())
            candidates = list(Path(tmp).glob('*.pdf'))
            if not candidates:
                raise RuntimeError('Aucun PDF généré par LibreOffice.')
            pdf = candidates[0]
            preview_name = f'system-{doc.systeme_id}-document-{doc.pk}.pdf'
            if doc.preview_pdf:
                try:
                    doc.preview_pdf.delete(save=False)
                except Exception:
                    pass
            with pdf.open('rb') as fh:
                doc.preview_pdf.save(preview_name, File(fh), save=False)
            doc.preview_status = 'ok'
            doc.preview_error = ''
            doc.save(update_fields=['preview_pdf', 'preview_status', 'preview_error', 'updated_at'])
            return True
    except Exception as exc:
        doc.preview_status = 'error'
        doc.preview_error = str(exc)[:2000]
        doc.save(update_fields=['preview_status', 'preview_error', 'updated_at'])
        return False


def _recompute_system_status_from_anomalies(systeme):
    if systeme.anomalies.filter(statut__in=['ouverte', 'en_cours'], blocking=True).exists() or systeme.anomalies.filter(statut__in=['ouverte', 'en_cours'], gravite='bloquante').exists():
        systeme.statut = 'hors_service'
    elif systeme.anomalies.filter(statut__in=['ouverte', 'en_cours']).exists():
        systeme.statut = 'alerte'
    elif systeme.sessions.filter(statut='ouverte').exists():
        systeme.statut = 'en_utilisation'
    else:
        systeme.statut = 'disponible'
    systeme.save(update_fields=['statut', 'updated_at'])


@system_login_required
def system_detail(request, pk):
    systeme = get_object_or_404(EducationalSystem.objects.select_related('zone', 'sous_zone', 'professeur_referent').prefetch_related('formations', 'niveaux'), pk=pk)
    user = current_system_user(request)
    visible_doc_filter = Q(actif=True)
    if not (user and user.is_prof_like):
        visible_doc_filter &= Q(visible_students=True, teacher_only=False)
    docs_sections = []
    for root in _root_document_sections():
        children = list(root.sous_categories.filter(active=True).order_by('ordre', 'code')) if hasattr(root, 'sous_categories') else []
        if not children:
            children = [root]
        child_rows = []
        for cat in children:
            qs = systeme.documents.filter(visible_doc_filter, categorie=cat).select_related('parent_document').prefetch_related('versions').order_by('titre')
            child_rows.append((cat, qs))
        root_docs = systeme.documents.filter(visible_doc_filter, categorie=root).select_related('parent_document').prefetch_related('versions').order_by('titre') if children and children[0] != root else []
        docs_sections.append((root, child_rows, root_docs))
    context = {
        'systeme': systeme,
        'effective_status': system_effective_status(systeme),
        'docs_sections': docs_sections,
        'uncategorized_docs': systeme.documents.filter(visible_doc_filter, categorie__isnull=True).select_related('parent_document').prefetch_related('versions'),
        'check_items': systeme.check_items.filter(actif=True).order_by('ordre', 'id'),
        'show_check_container': can_edit_systems(user, systeme),
        'can_download_original_docs': bool(user and (user.is_prof_like or can_edit_systems(user, systeme))),
        'my_open_sessions': systeme.sessions.filter(statut='ouverte', utilisateur=user).select_related('utilisateur') if user else [],
        'can_edit_this_system': can_edit_systems(user, systeme),
        'current_reservation': current_reservation_for_system(systeme),
        'upcoming_reservations': upcoming_reservations(systeme, 8),
        'open_sessions': systeme.sessions.filter(statut='ouverte').select_related('utilisateur'),
        'recent_sessions': systeme.sessions.select_related('utilisateur', 'formation', 'niveau', 'professeur_referent').order_by('-date_prise')[:10],
        'anomalies': systeme.anomalies.select_related('signalee_par', 'lift_requested_by', 'lift_authorized_by').order_by('-created_at')[:20],
        'maintenance_interventions': systeme.maintenance_interventions.select_related('intervention_par').order_by('-created_at')[:12],
        'change_logs': systeme.change_logs.select_related('effectue_par').order_by('-date_effet', '-created_at')[:100],
    }
    return render(request, 'system_manager/system_detail.html', context)


@system_admin_required
@require_http_methods(['GET', 'POST'])
def document_add(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    initial = {}
    cat = request.GET.get('categorie') or request.GET.get('category') or ''
    if cat and DocumentCategory.objects.filter(pk=cat).exists():
        initial['categorie'] = cat
    form = SystemDocumentForm(request.POST or None, request.FILES or None, initial=initial, systeme=systeme)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.systeme = systeme
        doc.ajoute_par = current_system_user(request)
        if doc.categorie and ('CORR' in doc.categorie.code.upper() or 'CORRECTION' in doc.categorie.nom.upper()):
            doc.teacher_only = True
            doc.visible_students = False
        try:
            doc.full_clean()
            doc.save()
            if _is_office_preview_candidate(doc):
                _generate_document_preview(doc)
            SystemChangeLog.objects.create(systeme=systeme, type_changement='document', titre=f'Ajout document : {doc.titre}', description=doc.description, version_apres=doc.version, effectue_par=current_system_user(request), date_effet=timezone.localdate())
            messages.success(request, 'Document ajouté.')
            return redirect('system_detail', systeme.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/document_form.html', {'form': form, 'title': f'Ajouter un document — {systeme.code}', 'systeme': systeme})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def document_update(request, pk):
    doc = get_object_or_404(SystemDocument.objects.select_related('systeme'), pk=pk)
    form = SystemDocumentForm(request.POST or None, request.FILES or None, instance=doc, systeme=doc.systeme)
    if request.method == 'POST' and form.is_valid():
        try:
            old_version = doc.version
            doc = form.save(commit=False)
            if doc.categorie and ('CORR' in doc.categorie.code.upper() or 'CORRECTION' in doc.categorie.nom.upper()):
                doc.teacher_only = True
                doc.visible_students = False
            doc.save()
            if _is_office_preview_candidate(doc) and (request.FILES.get('fichier') or not doc.preview_pdf):
                _generate_document_preview(doc)
            SystemChangeLog.objects.create(systeme=doc.systeme, type_changement='document', titre=f'Modification document : {doc.titre}', description=doc.description, version_avant=old_version, version_apres=doc.version, effectue_par=current_system_user(request), date_effet=timezone.localdate())
            messages.success(request, 'Document modifié.')
            return redirect('system_detail', doc.systeme.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/document_form.html', {'form': form, 'title': f'Modifier un document — {doc.systeme.code}', 'systeme': doc.systeme, 'document': doc})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def document_new_version(request, pk):
    old = get_object_or_404(SystemDocument.objects.select_related('systeme', 'categorie'), pk=pk)
    initial = {'categorie': old.categorie_id, 'titre': old.titre, 'type_document': old.type_document, 'parent_document': old.pk, 'description': old.description, 'visible_students': old.visible_students, 'teacher_only': old.teacher_only, 'actif': True}
    form = SystemDocumentForm(request.POST or None, request.FILES or None, initial=initial, systeme=old.systeme)
    if request.method == 'POST' and form.is_valid():
        doc = form.save(commit=False)
        doc.systeme = old.systeme
        doc.parent_document = old
        doc.ajoute_par = current_system_user(request)
        if doc.categorie and ('CORR' in doc.categorie.code.upper() or 'CORRECTION' in doc.categorie.nom.upper()):
            doc.teacher_only = True
            doc.visible_students = False
        try:
            doc.full_clean()
            doc.save()
            if _is_office_preview_candidate(doc):
                _generate_document_preview(doc)
            old.actif = False
            old.save(update_fields=['actif', 'updated_at'])
            SystemChangeLog.objects.create(systeme=old.systeme, type_changement='document', titre=f'Nouvelle version : {doc.titre}', description=f'Remplace le document #{old.pk}.', version_avant=old.version, version_apres=doc.version, effectue_par=current_system_user(request), date_effet=timezone.localdate())
            messages.success(request, 'Nouvelle version ajoutée. L’ancienne version est désactivée mais reste historisée.')
            return redirect('system_detail', old.systeme.pk)
        except ValidationError as exc:
            form.add_error(None, exc)
    return render(request, 'system_manager/document_form.html', {'form': form, 'title': f'Nouvelle version — {old.titre}', 'systeme': old.systeme, 'document': old})


def _check_items_for_phase(systeme, phase):
    return systeme.check_items.filter(actif=True).filter(Q(phase=phase) | Q(phase='deux')).order_by('ordre', 'id')


def _check_response_is_bad(item, value):
    if item.type_reponse != 'oui_non_nc':
        return False
    if not item.expected_response:
        return False
    return bool(value and value != item.expected_response)


def _save_check_responses(request, session, items, phase):
    created = []
    for item in items:
        resp = CheckResponse.objects.create(
            session=session,
            item=item,
            phase=phase,
            valeur=request.POST.get(f'item_{item.id}_value') or '',
            texte=request.POST.get(f'item_{item.id}_text') or '',
            photo=request.FILES.get(f'item_{item.id}_photo') if f'item_{item.id}_photo' in request.FILES else None,
        )
        created.append(resp)
    return created


def _create_anomalies_from_bad_checks(request, session, responses):
    anomalies = []
    for resp in responses:
        item = resp.item
        if not item or not _check_response_is_bad(item, resp.valeur):
            continue
        blocking = bool(item.bloquant_si_non)
        anomaly = SystemAnomaly.objects.create(
            systeme=session.systeme,
            session=session,
            signalee_par=current_system_user(request),
            titre=f'Check non conforme : {item.libelle}',
            description=f'Réponse attendue : {item.get_expected_response_display() or item.expected_response}. Réponse saisie : {resp.get_valeur_display() or resp.valeur}. ' + (resp.texte or ''),
            gravite='bloquante' if blocking else 'mineure',
            blocking=blocking,
            statut='ouverte',
        )
        anomalies.append(anomaly)
    return anomalies


@system_login_required
@require_http_methods(['GET', 'POST'])
def worksession_start(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    user = current_system_user(request)
    open_existing = WorkSession.objects.filter(systeme=systeme, utilisateur=user, statut='ouverte').order_by('-date_prise').first()
    if open_existing:
        messages.info(request, 'Une prise de poste est déjà ouverte pour ce système : passe directement à la restitution.')
        return redirect('worksession_return', open_existing.pk)
    current_reservation = current_reservation_for_system(systeme)
    initial = {'reservation': current_reservation, 'professeur_referent': systeme.professeur_referent_id}
    if current_reservation:
        initial.update({'professeur_referent': current_reservation.professeur_id, 'tp_code': current_reservation.tp_code, 'tp_titre': current_reservation.tp_titre})
    form = WorkSessionStartForm(request.POST or None, initial=initial)
    form.fields['reservation'].queryset = Reservation.objects.filter(systeme=systeme).exclude(statut__in=['annulee', 'refusee']).order_by('-date_debut')[:20]
    tp_suggestions = SystemTPAssociation.objects.filter(active=True, systeme=systeme).order_by('tp_titre').values_list('tp_code', 'tp_titre').distinct()[:200]
    items = _check_items_for_phase(systeme, 'prise')
    if request.method == 'POST' and form.is_valid():
        missing = _validate_check_post(request, items)
        if missing:
            for msg in missing:
                form.add_error(None, msg)
        else:
            session = form.save(commit=False)
            session.systeme = systeme
            session.utilisateur = user
            session.date_prise = timezone.now()
            session.statut = 'ouverte'
            if session.reservation:
                session.formation = session.reservation.formation
                session.classe_ou_groupe = session.reservation.classe_ou_groupe
            session.save()
            responses = _save_check_responses(request, session, items, 'prise')
            _create_anomalies_from_bad_checks(request, session, responses)
            if session.reservation:
                session.reservation.statut = 'en_cours'
                session.reservation.save(update_fields=['statut', 'updated_at'])
            systeme.statut = 'en_utilisation'
            systeme.save(update_fields=['statut', 'updated_at'])
            messages.success(request, 'Prise de poste enregistrée.')
            return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/worksession_start.html', {'systeme': systeme, 'form': form, 'items': items, 'current_reservation': current_reservation, 'tp_suggestions': tp_suggestions})


@system_login_required
@require_http_methods(['GET', 'POST'])
def worksession_return(request, pk):
    session = get_object_or_404(WorkSession.objects.select_related('systeme', 'reservation', 'utilisateur'), pk=pk)
    systeme = session.systeme
    form = WorkSessionReturnForm(request.POST or None, instance=session)
    items = _check_items_for_phase(systeme, 'restitution')
    if request.method == 'POST' and form.is_valid():
        missing = _validate_check_post(request, items)
        if missing:
            for msg in missing:
                form.add_error(None, msg)
        else:
            session = form.save(commit=False)
            session.date_restitution = timezone.now()
            responses = _save_check_responses(request, session, items, 'restitution')
            anomalies = _create_anomalies_from_bad_checks(request, session, responses)
            has_blocking = any(a.blocking for a in anomalies)
            has_any = bool(anomalies)
            session.statut = 'anomalie' if has_any else 'restituee'
            session.save()
            if session.reservation:
                session.reservation.statut = 'terminee' if session.statut == 'restituee' else 'non_restituee'
                session.reservation.save(update_fields=['statut', 'updated_at'])
            systeme.statut = 'hors_service' if has_blocking else ('alerte' if has_any else 'disponible')
            systeme.save(update_fields=['statut', 'updated_at'])
            messages.success(request, 'Restitution de poste enregistrée.')
            return redirect('system_detail', systeme.pk)
    return render(request, 'system_manager/worksession_return.html', {'session': session, 'systeme': systeme, 'form': form, 'items': items, 'session_anomalies': session.anomalies.exclude(statut__in=['resolue','annulee'])})


@system_login_required
def anomaly_detail(request, pk):
    anomaly = get_object_or_404(SystemAnomaly.objects.select_related('systeme', 'session', 'signalee_par', 'lift_requested_by', 'lift_authorized_by'), pk=pk)
    return render(request, 'system_manager/anomaly_detail.html', {'anomaly': anomaly, 'systeme': anomaly.systeme})


@system_login_required
@require_http_methods(['POST'])
def anomaly_request_lift(request, pk):
    anomaly = get_object_or_404(SystemAnomaly.objects.select_related('systeme'), pk=pk)
    user = current_system_user(request)
    comment = (request.POST.get('comment') or '').strip()
    if anomaly.blocking or anomaly.gravite == 'bloquante':
        anomaly.lift_requested_by = user
        anomaly.lift_requested_at = timezone.now()
        anomaly.lift_request_comment = comment
        anomaly.statut = 'en_cours'
        anomaly.save(update_fields=['lift_requested_by', 'lift_requested_at', 'lift_request_comment', 'statut', 'updated_at'])
        messages.warning(request, 'Demande de levée enregistrée. Une validation professeur/administrateur est nécessaire car l’anomalie est bloquante.')
    else:
        anomaly.statut = 'resolue'
        anomaly.action_realisee = comment or anomaly.action_realisee or 'Levée par utilisateur.'
        anomaly.date_resolution = timezone.now()
        anomaly.save(update_fields=['statut', 'action_realisee', 'date_resolution', 'updated_at'])
        _recompute_system_status_from_anomalies(anomaly.systeme)
        messages.success(request, 'Anomalie levée.')
    return redirect('system_anomaly_detail', anomaly.pk)


@system_edit_required
@require_http_methods(['POST'])
def anomaly_approve_lift(request, pk):
    anomaly = get_object_or_404(SystemAnomaly.objects.select_related('systeme'), pk=pk)
    user = current_system_user(request)
    if not (user and user.is_prof_like):
        messages.error(request, 'Validation réservée aux professeurs ou administrateurs.')
        return redirect('system_anomaly_detail', anomaly.pk)
    anomaly.statut = 'resolue'
    anomaly.lift_authorized_by = user
    anomaly.lift_authorized_at = timezone.now()
    anomaly.date_resolution = timezone.now()
    note = (request.POST.get('comment') or '').strip()
    if note:
        anomaly.action_realisee = note
    anomaly.save(update_fields=['statut', 'lift_authorized_by', 'lift_authorized_at', 'date_resolution', 'action_realisee', 'updated_at'])
    _recompute_system_status_from_anomalies(anomaly.systeme)
    messages.success(request, 'Levée d’anomalie validée.')
    return redirect('system_anomaly_detail', anomaly.pk)


@system_login_required
def dynamic_display(request):
    selected_zone = (request.GET.get('zone') or '').strip()
    selected_subzone = (request.GET.get('sous_zone') or '').strip()
    public_mode = (request.GET.get('mode') or '').strip().lower() == 'public'

    zones_filter = WorkshopZone.objects.filter(active=True).order_by('ordre_affichage', 'code')
    subzones_filter = WorkshopSubZone.objects.filter(active=True).select_related('zone').order_by('zone__ordre_affichage', 'zone__code', 'ordre_affichage', 'code')
    if selected_zone:
        subzones_filter = subzones_filter.filter(zone_id=selected_zone)

    zones = WorkshopZone.objects.filter(active=True).prefetch_related('systemes').order_by('ordre_affichage', 'code')
    if selected_zone:
        zones = zones.filter(id=selected_zone)
    if selected_subzone:
        zones = zones.filter(sous_zones__id=selected_subzone).distinct()

    open_sessions = WorkSession.objects.filter(statut='ouverte').select_related('systeme', 'systeme__zone', 'systeme__sous_zone', 'utilisateur').order_by('systeme__zone__ordre_affichage', 'systeme__code')
    anomalies = SystemAnomaly.objects.exclude(statut__in=['resolue', 'annulee']).select_related('systeme', 'systeme__zone', 'systeme__sous_zone', 'signalee_par').order_by('systeme__zone__ordre_affichage', '-blocking', '-created_at')
    if selected_zone:
        open_sessions = open_sessions.filter(systeme__zone_id=selected_zone)
        anomalies = anomalies.filter(systeme__zone_id=selected_zone)
    if selected_subzone:
        open_sessions = open_sessions.filter(systeme__sous_zone_id=selected_subzone)
        anomalies = anomalies.filter(systeme__sous_zone_id=selected_subzone)

    anomalies = list(anomalies)
    open_sessions = list(open_sessions)
    blocking_count = sum(1 for a in anomalies if a.blocking or a.gravite == 'bloquante')
    return render(request, 'system_manager/dynamic_display.html', {
        'zones': zones,
        'zones_filter': zones_filter,
        'subzones_filter': subzones_filter,
        'selected_zone': selected_zone,
        'selected_subzone': selected_subzone,
        'open_sessions': open_sessions,
        'anomalies': anomalies,
        'blocking_count': blocking_count,
        'public_mode': public_mode,
    })


@system_admin_required
@require_http_methods(['GET', 'POST'])
def temporary_permissions(request):
    edit_id = request.GET.get('edit') or ''
    instance = TemporarySystemPermission.objects.filter(pk=edit_id).first() if edit_id else None
    if request.method == 'POST':
        action = request.POST.get('form_action') or ''
        if action == 'delete_permissions':
            count = TemporarySystemPermission.objects.filter(pk__in=request.POST.getlist('selected_permissions')).delete()[0]
            messages.success(request, f'{count} droit(s) temporaire(s) supprimé(s).')
            return redirect('system_temporary_permissions')
        instance = TemporarySystemPermission.objects.filter(pk=request.POST.get('permission_id')).first() if request.POST.get('permission_id') else None
        form = TemporarySystemPermissionForm(request.POST, instance=instance)
        if form.is_valid():
            obj = form.save(commit=False)
            if not obj.user_id and not obj.school_class_id:
                form.add_error(None, 'Choisir au moins un utilisateur ou une classe.')
            else:
                obj.granted_by = current_system_user(request)
                obj.save()
                form.save_m2m()
                messages.success(request, 'Droit temporaire enregistré.')
                return redirect('system_temporary_permissions')
    else:
        form = TemporarySystemPermissionForm(instance=instance)
    return render(request, 'system_manager/temporary_permissions.html', {'form': form, 'edit_permission': instance, 'permissions': TemporarySystemPermission.objects.select_related('user', 'school_class', 'granted_by').prefetch_related('zones', 'systems').order_by('-date_debut')[:500], 'now': timezone.now()})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def default_check_create(request):
    form = DefaultCheckTemplateForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Check par défaut créé. Il sera appliqué aux prochains systèmes créés.')
        return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Créer un check par défaut'})


@system_admin_required
@require_http_methods(['GET', 'POST'])
def default_check_update(request, pk):
    obj = get_object_or_404(DefaultCheckTemplate, pk=pk)
    form = DefaultCheckTemplateForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Check par défaut modifié. Les systèmes déjà créés ne sont pas modifiés automatiquement.')
        return redirect('system_referentials')
    return render(request, 'system_manager/form.html', {'form': form, 'title': 'Modifier un check par défaut'})


def _protected_file_response(field_file, download_name=None, as_attachment=True):
    if not field_file:
        raise Http404('Fichier absent.')
    try:
        fh = field_file.open('rb')
    except Exception:
        raise Http404('Fichier introuvable.')
    return FileResponse(fh, as_attachment=as_attachment, filename=download_name or Path(field_file.name).name)


@system_login_required
def document_original_download(request, pk):
    doc = get_object_or_404(SystemDocument.objects.select_related('systeme', 'ajoute_par'), pk=pk, actif=True)
    user = current_system_user(request)
    if not (user and (user.is_prof_like or can_edit_systems(user, doc.systeme))):
        return HttpResponseForbidden('Téléchargement de l’original réservé aux professeurs, administrateurs ou créateurs/modificateurs autorisés.')
    return _protected_file_response(doc.fichier, as_attachment=True)


@system_login_required
def document_preview_download(request, pk):
    doc = get_object_or_404(SystemDocument.objects.select_related('systeme'), pk=pk, actif=True)
    user = current_system_user(request)
    if doc.teacher_only and not (user and user.is_prof_like):
        return HttpResponseForbidden('Document réservé aux professeurs.')
    return _protected_file_response(doc.preview_pdf, as_attachment=True)


@system_login_required
def api_tps(request):
    q = (request.GET.get('q') or '').strip()
    qs = SystemTPAssociation.objects.filter(active=True)
    if q:
        qs = qs.filter(Q(tp_code__icontains=q) | Q(tp_titre__icontains=q) | Q(sequence_titre__icontains=q) | Q(sequence_code__icontains=q))
    system_id = request.GET.get('systeme') or ''
    if system_id:
        qs = qs.filter(systeme_id=system_id)
    rows = qs.order_by('tp_titre').values('tp_code', 'tp_titre', 'sequence_code', 'sequence_titre').distinct()[:50]
    return JsonResponse({'results': list(rows)})


@system_login_required
def api_subzones(request):
    zone_id = request.GET.get('zone') or ''
    qs = WorkshopSubZone.objects.filter(active=True).select_related('zone').order_by('zone__code', 'ordre_affichage', 'code')
    if zone_id:
        qs = qs.filter(zone_id=zone_id)
    return JsonResponse({'results': [{'id': z.id, 'nom': z.nom, 'code': z.code, 'zone_id': z.zone_id} for z in qs]})

@system_edit_required
@require_http_methods(['GET', 'POST'])
def anomaly_create(request, system_pk):
    systeme = get_object_or_404(EducationalSystem, pk=system_pk)
    form = SystemAnomalyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        anomaly = form.save(commit=False)
        anomaly.systeme = systeme
        anomaly.signalee_par = current_system_user(request)
        if anomaly.gravite == 'bloquante':
            anomaly.blocking = True
        anomaly.save()
        _recompute_system_status_from_anomalies(systeme)
        SystemChangeLog.objects.create(systeme=systeme, type_changement='maintenance', titre=f'Anomalie : {anomaly.titre}', description=anomaly.description, effectue_par=current_system_user(request), date_effet=timezone.localdate())
        messages.success(request, 'Anomalie créée.')
        return redirect('system_anomaly_detail', anomaly.pk)
    return render(request, 'system_manager/form.html', {'form': form, 'title': f'Signaler une anomalie — {systeme.code}'})
