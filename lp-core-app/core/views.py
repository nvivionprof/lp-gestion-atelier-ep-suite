from django.conf import settings
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods
from pathlib import Path
import os
import csv
import tempfile
import requests
import json
import zipfile
import hashlib
from datetime import datetime
from django.utils.text import get_valid_filename
from .models import CoreUser, CoreFormation, CoreClass, CoreStore, CoreUserStoreAccess, CoreCertification, CoreRightDefinition, CoreCertificationType, CoreUserDocument, RgpdPolicySettings, CoreAuditLog, PublicSuiteSettings, BackupPolicySettings, UploadedUpdatePackage, SuiteMaintenanceJob, CoreModuleAccessRule, CoreAtelierBlock, CoreAtelierBlockSlot, CoreWorkshopZone, CoreWorkshopSubZone, normalize_code
from .importers import import_users_xlsx


def current_core_user(request):
    uid = request.session.get('core_user_id')
    if not uid:
        return None
    user = CoreUser.objects.filter(id=uid, active=True).first()
    if user is None:
        request.session.pop('core_user_id', None)
        request.session.modified = True
    return user


def require_core_admin(request):
    user = current_core_user(request)
    if not user or not user.is_admin_like:
        messages.error(request, 'Accès réservé à l’administration LP Core.')
        return None
    return user

def can_edit_user_profile(actor, target):
    if not actor:
        return False
    if actor.is_admin_like:
        return True
    return actor.pk == target.pk


def log_core_action(actor, action, target='', details=''):
    try:
        CoreAuditLog.objects.create(actor=actor, action=action, target=str(target or ''), details=str(details or ''))
    except Exception:
        pass


def certification_type_choices():
    dynamic = [(c.code, c.label) for c in CoreCertificationType.objects.filter(active=True).order_by('code')]
    static = list(CoreCertification.TYPE_CHOICES)
    codes = {c for c, _ in dynamic}
    return dynamic + [(c, l) for c, l in static if c not in codes]


def api_allowed(request):
    token = request.headers.get('X-API-Key') or request.GET.get('token')
    if settings.LP_CORE_API_TOKEN and token != settings.LP_CORE_API_TOKEN:
        return False
    return True


def dashboard(request):
    user = current_core_user(request)
    if not user:
        return redirect('core_login')
    context = {
        'users_count': CoreUser.objects.count(),
        'active_users_count': CoreUser.objects.filter(active=True).count(),
        'classes_count': CoreClass.objects.count(),
        'formations_count': CoreFormation.objects.count(),
        'recent_users': CoreUser.objects.order_by('-updated_at')[:8],
        'user': user,
    }
    return render(request, 'core/dashboard.html', context)


@require_http_methods(['GET', 'POST'])
def login_view(request):
    if current_core_user(request):
        return redirect('core_dashboard')
    if request.method == 'POST':
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        user = CoreUser.objects.filter(Q(username=username) | Q(code=username), active=True).first()
        if user and user.check_password(password):
            request.session.cycle_key()
            request.session['core_user_id'] = user.id
            request.session.modified = True
            messages.success(request, f'Connexion LP Core : {user.first_name} {user.last_name}.')
            if getattr(user, 'force_password_change', False):
                messages.warning(request, 'Changement du mot de passe obligatoire avant de poursuivre.')
                return redirect('core_my_account')
            return redirect('core_dashboard')
        messages.error(request, 'Identifiant ou mot de passe incorrect.')
    return render(request, 'core/login.html')


def logout_view(request):
    request.session.pop('core_user_id', None)
    messages.success(request, 'Déconnexion LP Core effectuée.')
    return redirect('core_login')


def users_list(request):
    if not require_core_admin(request):
        return redirect('core_login')
    q = (request.GET.get('q') or '').strip()
    users = CoreUser.objects.select_related('formation').all()
    if q:
        users = users.filter(last_name__icontains=q) | users.filter(first_name__icontains=q) | users.filter(code__icontains=q) | users.filter(username__icontains=q) | users.filter(class_name__icontains=q)
    return render(request, 'core/users_list.html', {'users': users[:500], 'q': q})


@require_http_methods(['GET', 'POST'])
def users_import(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    report = None
    if request.method == 'POST':
        file = request.FILES.get('file')
        if not file:
            messages.error(request, 'Aucun fichier reçu.')
        else:
            suffix = Path(file.name).suffix or '.xlsx'
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                for chunk in file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name
            report = import_users_xlsx(tmp_path, actor=actor, source='upload')
            if report['errors']:
                messages.warning(request, f"Import terminé avec {len(report['errors'])} erreur(s).")
            else:
                messages.success(request, f"Import terminé : {report['created']} créés, {report['updated']} mis à jour.")
    return render(request, 'core/users_import.html', {'report': report})




def _module_sync_timeout():
    try:
        return int(getattr(settings, 'MODULE_SYNC_TIMEOUT_SECONDS', 90) or 90)
    except Exception:
        return 90


def _module_sync_headers_and_data(extra=None):
    token = getattr(settings, 'LP_CORE_API_TOKEN', '') or ''
    headers = {'X-API-Key': token} if token else {}
    data = dict(extra or {})
    # Double transmission volontaire : certains anciens endpoints lisent le POST,
    # d'autres l'en-tête. Cela évite les HTTP 403 lors des upgrades mixtes.
    if token:
        data.setdefault('token', token)
    return headers, data


def _sync_endpoint(module_name, url, *, core_user_id=None, force_password=False, timeout=None):
    timeout = timeout or _module_sync_timeout()
    payload = {}
    if core_user_id:
        payload['core_user_id'] = str(core_user_id)
    if force_password:
        payload['force_password'] = '1'
    headers, data = _module_sync_headers_and_data(payload)
    response = requests.post(url, headers=headers, data=data, timeout=timeout)
    result = {'module': module_name, 'ok': False, 'status': response.status_code, 'url': url, 'payload': None, 'error': ''}
    try:
        result['payload'] = response.json()
    except Exception:
        result['payload'] = {'text': response.text[:800]}
    if response.ok:
        result['ok'] = bool(result['payload'].get('ok', True)) if isinstance(result['payload'], dict) else True
        if not result['ok']:
            result['error'] = str(result['payload'])[:800]
    else:
        result['error'] = f'HTTP {response.status_code} — {response.text[:300]}'
    return result


def _sync_modules_from_core(*, modules=None, core_user_id=None, force_password=False):
    all_modules = [
        ('ToolMag', getattr(settings, 'TOOLMAG_INTERNAL_SYNC_URL', 'http://toolmag-app:8000/api/internal/sync-lp-core/')),
        ('PedaShop', getattr(settings, 'PEDASHOP_INTERNAL_SYNC_URL', 'http://pedashop-app:8000/api/internal/sync-lp-core/')),
        ('Safety Manager', getattr(settings, 'SAFETY_INTERNAL_SYNC_URL', 'http://safety-app:8000/sync-lp-core/')),
        ('System Manager', getattr(settings, 'SYSTEM_MANAGER_INTERNAL_SYNC_URL', 'http://system-manager-app:8000/sync-lp-core/')),
        ('TP Manager', getattr(settings, 'TPMANAGER_INTERNAL_SYNC_URL', 'http://tpmanager-app:8000/sync-lp-core/')),
        ('PFMP Manager', getattr(settings, 'PFMP_INTERNAL_SYNC_URL', 'http://pfmp-app:8000/sync-lp-core/')),
    ]
    if modules:
        wanted = {m.lower() for m in modules}
        all_modules = [(n, u) for n, u in all_modules if n.lower() in wanted]
    results = []
    for name, url in all_modules:
        try:
            results.append(_sync_endpoint(name, url, core_user_id=core_user_id, force_password=force_password))
        except Exception as exc:
            results.append({'module': name, 'ok': False, 'status': None, 'url': url, 'payload': None, 'error': str(exc)})
    return results


def _report_sync_messages(request, results, *, prefix='Synchronisation'):
    ok_results = [r for r in results if r.get('ok')]
    errors = [r for r in results if not r.get('ok')]
    if errors:
        details = ' | '.join(f"{r['module']}: {r.get('error') or r.get('payload')}" for r in errors)
        messages.warning(request, f"{prefix} partielle : {len(ok_results)} module(s) OK ; erreurs : {details}")
    else:
        modules = ', '.join(r['module'] for r in ok_results)
        messages.success(request, f"{prefix} terminée : {modules or 'aucun module' }.")
    return {'ok': len(ok_results), 'errors': errors}


@require_http_methods(['POST'])
def sync_toolmag_from_core(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    result = _sync_endpoint('ToolMag', getattr(settings, 'TOOLMAG_INTERNAL_SYNC_URL', 'http://toolmag-app:8000/api/internal/sync-lp-core/'))
    _report_sync_messages(request, [result], prefix='Synchronisation ToolMag')
    log_core_action(actor, 'SYNC_TOOLMAG', 'ToolMag', str(result)[:1000])
    return redirect('core_users_import')


@require_http_methods(['POST'])
def sync_pedashop_from_core(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    result = _sync_endpoint('PedaShop', getattr(settings, 'PEDASHOP_INTERNAL_SYNC_URL', 'http://pedashop-app:8000/api/internal/sync-lp-core/'))
    _report_sync_messages(request, [result], prefix='Synchronisation PedaShop')
    log_core_action(actor, 'SYNC_PEDASHOP', 'PedaShop', str(result)[:1000])
    return redirect('core_users_import')


def _sync_module_from_core(request, module_name, setting_name, default_url, redirect_name='core_users_import'):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    result = _sync_endpoint(module_name, getattr(settings, setting_name, default_url))
    _report_sync_messages(request, [result], prefix=f'Synchronisation {module_name}')
    log_core_action(actor, f'SYNC_{module_name.upper()}', module_name, str(result)[:1000])
    return redirect(redirect_name)


@require_http_methods(['POST'])
def sync_safety_from_core(request):
    return _sync_module_from_core(request, 'Safety Manager', 'SAFETY_INTERNAL_SYNC_URL', 'http://safety-app:8000/sync-lp-core/')


@require_http_methods(['POST'])
def sync_system_manager_from_core(request):
    return _sync_module_from_core(request, 'System Manager', 'SYSTEM_MANAGER_INTERNAL_SYNC_URL', 'http://system-manager-app:8000/sync-lp-core/')


@require_http_methods(['POST'])
def sync_tpmanager_from_core(request):
    return _sync_module_from_core(request, 'TP Manager', 'TPMANAGER_INTERNAL_SYNC_URL', 'http://tpmanager-app:8000/sync-lp-core/')


@require_http_methods(['POST'])
def sync_pfmp_from_core(request):
    return _sync_module_from_core(request, 'PFMP Manager', 'PFMP_INTERNAL_SYNC_URL', 'http://pfmp-app:8000/sync-lp-core/')


@require_http_methods(['POST'])
def sync_all_modules_from_core(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    results = _sync_modules_from_core()
    report = _report_sync_messages(request, results, prefix='Synchronisation globale')
    log_core_action(actor, 'SYNC_ALL_MODULES', 'modules', f"ok={report['ok']}; errors={report['errors']}")
    return redirect('core_users_import')

def users_export_csv(request):
    if not require_core_admin(request):
        return redirect('core_login')
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = 'attachment; filename="lp_core_users_export.csv"'
    response.write('\ufeff')
    writer = csv.writer(response, delimiter=';')
    writer.writerow(['code', 'identifiant', 'nom', 'prenom', 'classe', 'formation', 'groupe', 'role', 'droits', 'actif'])
    for u in CoreUser.objects.select_related('formation').all():
        writer.writerow([u.code, u.username, u.last_name, u.first_name, u.class_name, u.formation.code if u.formation else '', u.group_name, u.role_principal, u.rights, int(u.active)])
    return response


def user_payload(u):
    payload = {
        'id': u.id,
        'code': u.code,
        'username': u.username,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'email': u.email,
        'formation_code': u.formation.code if u.formation else '',
        'formation_name': u.formation.name if u.formation else '',
        'class_name': u.class_name,
        'group_name': u.group_name,
        'role_principal': u.role_principal,
        'rights': u.rights,
        'active': u.active,
        'school_year': u.school_year,
        'personal_email': u.personal_email,
        'personal_phone': u.personal_phone,
        'image_consent_status': u.image_consent_status,
        'parent_image_opposition': u.parent_image_opposition,
        'personal_upload_blocked': u.personal_upload_blocked,
        'identity_photo_url': u.identity_photo.url if u.display_photo_allowed() else '',
        'identity_photo_placeholder': u.image_placeholder_text(),
        'pedashop_magasins': [
            {'code': a.store.code, 'nom': a.store.nom}
            for a in u.store_accesses.select_related('store').filter(active=True, store__active=True, store__module='pedashop')
        ],
        'certifications': [
            {
                'type': c.type_certification,
                'niveau': c.niveau,
                'date_obtention': c.date_obtention.isoformat() if c.date_obtention else '',
                'date_fin_validite': c.date_fin_validite.isoformat() if c.date_fin_validite else '',
                'actif': c.actif,
            }
            for c in u.certifications.filter(actif=True)
        ],
    }
    if settings.LP_CORE_EXPOSE_INITIAL_PASSWORD_FOR_SYNC:
        payload['initial_password'] = u.initial_password_for_sync
    return payload


def api_health(request):
    return JsonResponse({'status': 'ok', 'service': 'lp-core', 'version': settings.LP_CORE_VERSION})


def api_users(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    users = CoreUser.objects.select_related('formation').filter(active=True).order_by('last_name', 'first_name')
    return JsonResponse({'results': [user_payload(u) for u in users]})


def api_user_detail(request, user_id):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    u = CoreUser.objects.select_related('formation').get(id=user_id)
    return JsonResponse(user_payload(u))


def api_classes(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    data = [{'id': c.id, 'name': c.name, 'formation_code': c.formation.code if c.formation else '', 'school_year': c.school_year, 'active': c.active} for c in CoreClass.objects.select_related('formation').all()]
    return JsonResponse({'results': data})


def api_formations(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    data = [{'id': f.id, 'code': f.code, 'name': f.name, 'active': f.active} for f in CoreFormation.objects.all()]
    return JsonResponse({'results': data})



@require_http_methods(['GET', 'POST'])
def user_detail(request, pk):
    """Fiche utilisateur LP Core : droits, magasins, profil, image et habilitations."""
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    user = get_object_or_404(CoreUser.objects.select_related('formation'), pk=pk)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_rights':
            selected_rights = request.POST.getlist('rights_codes')
            # Compatibilité : on conserve aussi la zone texte si présente.
            extra_rights = [r.strip() for r in (request.POST.get('rights_extra') or '').replace(',', ';').split(';') if r.strip()]
            user.rights = ';'.join(sorted(set(selected_rights + extra_rights)))
            user.role_principal = request.POST.get('role_principal', user.role_principal)
            user.save(update_fields=['rights', 'role_principal', 'updated_at'])
            log_core_action(actor, 'UPDATE_USER_RIGHTS', user.code, user.rights)
            messages.success(request, 'Droits et rôle mis à jour.')
        elif action == 'reset_password':
            new_password = (request.POST.get('new_password') or '').strip()
            confirm_password = (request.POST.get('confirm_password') or '').strip()
            sync_modules = request.POST.get('sync_modules') == '1'
            force_change = request.POST.get('force_password_change') == '1'
            if not new_password:
                messages.error(request, 'Mot de passe non renseigné.')
            elif new_password != confirm_password:
                messages.error(request, 'Les deux mots de passe ne correspondent pas.')
            elif len(new_password) < 4:
                messages.error(request, 'Mot de passe trop court : 4 caractères minimum.')
            else:
                user.set_password(new_password)
                user.initial_password_for_sync = new_password
                user.force_password_change = force_change
                user.save(update_fields=['password_hash', 'initial_password_for_sync', 'force_password_change', 'updated_at'])
                log_core_action(actor, 'RESET_USER_PASSWORD', user.code, f'sync_modules={sync_modules}; force_change={force_change}')
                messages.success(request, f'Mot de passe réinitialisé pour {user.code}.')
                if sync_modules:
                    results = _sync_modules_from_core(core_user_id=user.id, force_password=True)
                    _report_sync_messages(request, results, prefix=f'Resynchronisation mot de passe {user.code}')
        elif action == 'update_profile':
            user.personal_email = request.POST.get('personal_email', '')
            user.personal_phone = request.POST.get('personal_phone', '')
            user.image_consent_status = request.POST.get('image_consent_status') or user.image_consent_status
            user.image_consent_comment = request.POST.get('image_consent_comment', '')
            user.parent_image_opposition = request.POST.get('parent_image_opposition') == '1'
            user.personal_upload_blocked = request.POST.get('personal_upload_blocked') == '1' or user.parent_image_opposition
            if user.parent_image_opposition:
                user.image_consent_status = 'refused'
            photo = request.FILES.get('identity_photo')
            if photo:
                if user.parent_image_opposition or user.personal_upload_blocked or user.image_consent_status == 'refused':
                    messages.error(request, 'Photo refusée : opposition parentale ou blocage RGPD actif.')
                    log_core_action(actor, 'BLOCK_PHOTO_UPLOAD', user.code, 'Opposition ou blocage actif')
                else:
                    user.identity_photo = photo
                    if user.image_consent_status == 'unknown':
                        user.image_consent_status = 'authorized'
                        user.image_consent_comment = (user.image_consent_comment or 'Autorisation image positionnée lors de l’ajout de la photo dans LP Core.').strip()
                    log_core_action(actor, 'UPLOAD_IDENTITY_PHOTO', user.code, 'Photo d’identité mise à jour')
            user.save()
            messages.success(request, 'Profil RGPD / photo mis à jour.')
        elif action == 'add_document':
            if user.personal_upload_blocked:
                messages.error(request, 'Ajout de document bloqué pour cet utilisateur.')
                log_core_action(actor, 'BLOCK_DOCUMENT_UPLOAD', user.code, 'personal_upload_blocked')
            else:
                file = request.FILES.get('document_file')
                if file:
                    CoreUserDocument.objects.create(
                        user=user,
                        type_document=request.POST.get('type_document') or 'autre',
                        title=request.POST.get('document_title') or file.name,
                        file=file,
                        visible_to_prof=bool(request.POST.get('visible_to_prof')),
                        visible_to_admin=True,
                        uploaded_by=actor,
                    )
                    log_core_action(actor, 'UPLOAD_USER_DOCUMENT', user.code, file.name)
                    messages.success(request, 'Document personnel ajouté.')
        elif action == 'add_store':
            for store_id in request.POST.getlist('stores'):
                store = get_object_or_404(CoreStore, pk=store_id)
                access, _ = CoreUserStoreAccess.objects.get_or_create(user=user, store=store)
                access.active = True
                access.save()
            messages.success(request, 'Magasin(s) affecté(s).')
        elif action == 'remove_store':
            access = get_object_or_404(CoreUserStoreAccess, pk=request.POST.get('access_id'), user=user)
            access.delete()
            messages.success(request, 'Magasin retiré.')
        elif action == 'add_certification':
            CoreCertification.objects.create(
                user=user,
                type_certification=request.POST.get('type_certification') or 'AUTRE',
                niveau=request.POST.get('niveau', ''),
                date_obtention=request.POST.get('date_obtention') or None,
                date_fin_validite=request.POST.get('date_fin_validite') or None,
                actif=True,
                commentaire=request.POST.get('commentaire', ''),
            )
            messages.success(request, 'Habilitation / certification ajoutée.')
        elif action == 'toggle_certification':
            cert = get_object_or_404(CoreCertification, pk=request.POST.get('certification_id'), user=user)
            cert.actif = not cert.actif
            cert.save(update_fields=['actif', 'updated_at'])
            messages.success(request, 'Statut certification modifié.')
        return redirect('core_user_detail', pk=user.pk)
    rights_defs = CoreRightDefinition.objects.filter(active=True).order_by('module', 'code')
    context = {
        'target_user': user,
        'all_roles': CoreUser.ROLE_CHOICES,
        'stores': CoreStore.objects.filter(active=True).order_by('module', 'code'),
        'store_accesses': user.store_accesses.select_related('store').all(),
        'certifications': user.certifications.all(),
        'certification_types': certification_type_choices(),
        'rights_defs': rights_defs,
        'user_rights': set(user.rights_list()),
        'documents': user.personal_documents.all(),
        'document_types': CoreUserDocument.DOC_TYPE_CHOICES,
    }
    return render(request, 'core/user_detail.html', context)


@require_http_methods(['GET', 'POST'])
def stores_list(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    if request.method == 'POST':
        form_action = request.POST.get('form_action') or 'store'
        if form_action == 'store':
            code = request.POST.get('code', '')
            nom = request.POST.get('nom', '')
            module = request.POST.get('module') or 'global'
            if code and nom:
                store, created = CoreStore.objects.get_or_create(module=module, code=code, defaults={'nom': nom})
                store.nom = nom
                store.description = request.POST.get('description', '')
                store.active = bool(request.POST.get('active', '1'))
                store.save()
                messages.success(request, f"Magasin {'créé' if created else 'mis à jour'} : {store.code}. Il sera synchronisable vers tous les modules.")
        elif form_action == 'right':
            code = request.POST.get('right_code', '')
            label = request.POST.get('right_label', '')
            if code and label:
                right, _ = CoreRightDefinition.objects.get_or_create(code=code, defaults={'label': label})
                right.label = label
                right.module = request.POST.get('right_module') or 'global'
                right.description = request.POST.get('right_description', '')
                right.active = request.POST.get('right_active', '1') == '1'
                right.save()
                messages.success(request, f'Droit enregistré : {right.code}.')
        elif form_action == 'module_rule':
            module = request.POST.get('module_code') or ''
            target_type = request.POST.get('target_type') or ''
            target_value = (request.POST.get('target_value') or '').strip()
            if module and target_type and target_value:
                rule, _ = CoreModuleAccessRule.objects.get_or_create(module=module, target_type=target_type, target_value=target_value)
                rule.active = request.POST.get('rule_active', '1') == '1'
                rule.comment = request.POST.get('rule_comment', '')
                rule.save()
                messages.success(request, f'Règle d’accès module enregistrée : {rule}.')
            else:
                messages.error(request, 'Module, cible et valeur sont obligatoires pour une règle d’accès.')
        elif form_action == 'delete_module_rule':
            rid = request.POST.get('rule_id')
            CoreModuleAccessRule.objects.filter(pk=rid).delete()
            messages.success(request, 'Règle d’accès module supprimée.')
        elif form_action == 'cert_type':
            code = request.POST.get('cert_code', '')
            label = request.POST.get('cert_label', '')
            if code and label:
                cert, _ = CoreCertificationType.objects.get_or_create(code=code, defaults={'label': label})
                cert.label = label
                cert.description = request.POST.get('cert_description', '')
                cert.active = request.POST.get('cert_active', '1') == '1'
                cert.save()
                messages.success(request, f'Type de certification enregistré : {cert.code}.')
        return redirect('core_stores_list')
    return render(request, 'core/stores_list.html', {
        'stores': CoreStore.objects.all(),
        'modules': CoreStore.MODULE_CHOICES,
        'rights': CoreRightDefinition.objects.all(),
        'right_modules': CoreRightDefinition.MODULE_CHOICES,
        'cert_types': CoreCertificationType.objects.all(),
        'module_rules': CoreModuleAccessRule.objects.all(),
        'module_choices': CoreModuleAccessRule.MODULE_CHOICES,
        'target_choices': CoreModuleAccessRule.TARGET_CHOICES,
    })


@require_http_methods(['GET', 'POST'])
def bulk_permissions(request):
    """Affectation par lot des droits, magasins, habilitations et statuts image RGPD."""
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    users = CoreUser.objects.select_related('formation').all()
    q = (request.GET.get('q') or request.POST.get('q') or '').strip()
    class_name = request.GET.get('class_name') or request.POST.get('class_name') or ''
    formation = request.GET.get('formation') or request.POST.get('formation') or ''
    role = request.GET.get('role') or request.POST.get('role') or ''
    if q:
        users = users.filter(Q(code__icontains=q) | Q(last_name__icontains=q) | Q(first_name__icontains=q) | Q(username__icontains=q))
    if class_name:
        users = users.filter(class_name=class_name)
    if formation:
        users = users.filter(formation__code=formation)
    if role:
        users = users.filter(role_principal=role)
    filtered_users = users.order_by('class_name', 'last_name', 'first_name')[:800]
    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_users')
        target_qs = CoreUser.objects.filter(id__in=selected_ids) if selected_ids else users
        action = request.POST.get('bulk_action')
        if action in {'add_right', 'remove_right'}:
            selected_rights = request.POST.getlist('rights_codes')
            if selected_rights:
                for u in target_qs:
                    rights = set(u.rights_list())
                    if action == 'add_right':
                        rights.update(selected_rights)
                    else:
                        rights.difference_update(selected_rights)
                    u.rights = ';'.join(sorted(rights))
                    u.save(update_fields=['rights', 'updated_at'])
                messages.success(request, f'Droits mis à jour sur {target_qs.count()} utilisateur(s).')
                log_core_action(actor, action.upper(), 'bulk', ';'.join(selected_rights))
        elif action in {'add_store', 'remove_store'}:
            store_ids = request.POST.getlist('stores')
            if store_ids:
                if action == 'add_store':
                    for store in CoreStore.objects.filter(id__in=store_ids):
                        for u in target_qs:
                            access, _ = CoreUserStoreAccess.objects.get_or_create(user=u, store=store)
                            access.active = True
                            access.save()
                    messages.success(request, 'Magasin(s) affecté(s) au lot.')
                else:
                    CoreUserStoreAccess.objects.filter(user__in=target_qs, store_id__in=store_ids).delete()
                    messages.success(request, 'Magasin(s) retiré(s) du lot.')
        elif action == 'add_certification':
            cert_type = request.POST.get('type_certification') or 'AUTRE'
            niveau = request.POST.get('niveau', '')
            date_obtention = request.POST.get('date_obtention') or None
            date_fin = request.POST.get('date_fin_validite') or None
            for u in target_qs:
                CoreCertification.objects.create(user=u, type_certification=cert_type, niveau=niveau, date_obtention=date_obtention, date_fin_validite=date_fin, actif=True)
            messages.success(request, 'Certification / habilitation ajoutée au lot.')
        elif action == 'set_image_authorization':
            status = request.POST.get('image_consent_status') or 'unknown'
            parent_refusal = request.POST.get('parent_image_opposition') == '1'
            block_uploads = request.POST.get('personal_upload_blocked') == '1' or parent_refusal
            for u in target_qs:
                u.image_consent_status = 'refused' if parent_refusal else status
                u.parent_image_opposition = parent_refusal
                u.personal_upload_blocked = block_uploads
                u.image_consent_comment = request.POST.get('image_consent_comment', '')
                u.save(update_fields=['image_consent_status', 'parent_image_opposition', 'personal_upload_blocked', 'image_consent_comment', 'updated_at'])
            messages.success(request, 'Statut droit à l’image / blocage upload appliqué au lot.')
            log_core_action(actor, 'BULK_IMAGE_CONSENT', 'bulk', f'status={status}; parent_refusal={parent_refusal}; block={block_uploads}')
        return redirect(f'{request.path}?q={q}&class_name={class_name}&formation={formation}&role={role}')
    context = {
        'users': filtered_users,
        'q': q,
        'class_name': class_name,
        'formation': formation,
        'role': role,
        'classes': CoreUser.objects.exclude(class_name='').values_list('class_name', flat=True).distinct().order_by('class_name'),
        'formations': CoreFormation.objects.filter(active=True),
        'roles': CoreUser.ROLE_CHOICES,
        'stores': CoreStore.objects.filter(active=True).order_by('module', 'code'),
        'certification_types': certification_type_choices(),
        'rights_defs': CoreRightDefinition.objects.filter(active=True).order_by('module', 'code'),
    }
    return render(request, 'core/bulk_permissions.html', context)



@require_http_methods(['GET', 'POST'])
def student_lifecycle(request):
    """Gestion centralisée des élèves : montée de niveau, changement de classe/groupe et activation par lot."""
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')

    q = (request.GET.get('q') or request.POST.get('q') or '').strip()
    class_name = (request.GET.get('class_name') or request.POST.get('class_name') or '').strip()
    formation_code = (request.GET.get('formation') or request.POST.get('formation') or '').strip()
    role = (request.GET.get('role') or request.POST.get('role') or '').strip()
    active_filter = (request.GET.get('active') or request.POST.get('active') or 'active').strip()

    users_qs = CoreUser.objects.select_related('formation').all()
    if q:
        users_qs = users_qs.filter(Q(code__icontains=q) | Q(username__icontains=q) | Q(last_name__icontains=q) | Q(first_name__icontains=q) | Q(class_name__icontains=q))
    if class_name:
        users_qs = users_qs.filter(class_name=class_name)
    if formation_code:
        users_qs = users_qs.filter(formation__code=formation_code)
    if role:
        users_qs = users_qs.filter(role_principal=role)
    if active_filter == 'active':
        users_qs = users_qs.filter(active=True)
    elif active_filter == 'inactive':
        users_qs = users_qs.filter(active=False)

    filtered_users = users_qs.order_by('formation__code', 'class_name', 'last_name', 'first_name')[:900]

    if request.method == 'POST':
        selected_ids = request.POST.getlist('selected_users')
        apply_filtered = request.POST.get('apply_filtered') == '1'
        target_qs = CoreUser.objects.filter(id__in=selected_ids) if selected_ids else (users_qs if apply_filtered else CoreUser.objects.none())
        count = target_qs.count()
        if count == 0:
            messages.error(request, 'Aucun élève/utilisateur sélectionné. Coche des lignes ou active “appliquer au filtre”.')
        else:
            new_formation_code = (request.POST.get('new_formation') or '').strip()
            new_class_name = (request.POST.get('new_class_name') or '').strip()
            new_group_name = (request.POST.get('new_group_name') or '').strip()
            new_school_year = (request.POST.get('new_school_year') or '').strip()
            new_role = (request.POST.get('new_role') or '').strip()
            new_active = request.POST.get('new_active') or ''
            sync_after = request.POST.get('sync_modules') == '1'

            formation = None
            if new_formation_code:
                formation = CoreFormation.objects.filter(code=new_formation_code, active=True).first()
                if not formation:
                    messages.error(request, f'Formation inconnue : {new_formation_code}')
                    return redirect(request.path)

            updated = 0
            for u in target_qs.select_related('formation'):
                fields = ['updated_at']
                if formation is not None:
                    u.formation = formation
                    fields.append('formation')
                if new_class_name:
                    u.class_name = new_class_name
                    fields.append('class_name')
                if request.POST.get('change_group') == '1':
                    u.group_name = new_group_name
                    fields.append('group_name')
                if new_school_year:
                    u.school_year = new_school_year
                    fields.append('school_year')
                if new_role:
                    u.role_principal = new_role
                    fields.append('role_principal')
                if new_active in {'1', '0'}:
                    u.active = (new_active == '1')
                    fields.append('active')
                u.save(update_fields=fields)
                if u.formation and u.class_name:
                    CoreClass.objects.get_or_create(formation=u.formation, name=u.class_name, school_year=u.school_year or '')
                updated += 1

            messages.success(request, f'Gestion élèves LP Core : {updated} utilisateur(s) mis à jour.')
            log_core_action(actor, 'STUDENT_LIFECYCLE_BULK', 'bulk', f'updated={updated}; class={new_class_name}; formation={new_formation_code}; school_year={new_school_year}; active={new_active}')
            if sync_after:
                results = _sync_modules_from_core()
                _report_sync_messages(request, results, prefix='Synchronisation après gestion élèves')
        return redirect(f'{request.path}?q={q}&class_name={class_name}&formation={formation_code}&role={role}&active={active_filter}')

    return render(request, 'core/student_lifecycle.html', {
        'users': filtered_users,
        'q': q,
        'class_name': class_name,
        'formation': formation_code,
        'role': role,
        'active_filter': active_filter,
        'classes': CoreUser.objects.exclude(class_name='').values_list('class_name', flat=True).distinct().order_by('class_name'),
        'formations': CoreFormation.objects.filter(active=True).order_by('code'),
        'roles': CoreUser.ROLE_CHOICES,
    })

@require_http_methods(['GET', 'POST'])
def my_account(request):
    actor = current_core_user(request)
    if not actor:
        messages.error(request, 'Connexion requise.')
        return redirect('core_login')
    if request.method == 'POST':
        new_password = request.POST.get('new_password') or ''
        new_password2 = request.POST.get('new_password2') or ''
        if new_password or new_password2:
            if len(new_password) < 4:
                messages.error(request, 'Mot de passe trop court : 4 caractères minimum.')
                return redirect('core_my_account')
            if new_password != new_password2:
                messages.error(request, 'Les deux mots de passe ne correspondent pas.')
                return redirect('core_my_account')
            actor.set_password(new_password)
            actor.initial_password_for_sync = new_password
            actor.force_password_change = False
            actor.save()
            messages.success(request, 'Mot de passe LP Core modifié.')
            return redirect('core_my_account')
        actor.personal_email = request.POST.get('personal_email', '')
        actor.personal_phone = request.POST.get('personal_phone', '')
        posted_consent = request.POST.get('image_consent_status')
        if posted_consent in {'unknown', 'authorized', 'refused'} and not actor.parent_image_opposition:
            actor.image_consent_status = posted_consent
        if not actor.personal_upload_blocked and not actor.parent_image_opposition and actor.image_consent_status != 'refused':
            photo = request.FILES.get('identity_photo')
            if photo:
                actor.identity_photo = photo
                if actor.image_consent_status == 'unknown':
                    actor.image_consent_status = 'authorized'
                    actor.image_consent_comment = (actor.image_consent_comment or 'Autorisation image positionnée lors de l’ajout de la photo par l’utilisateur.').strip()
                log_core_action(actor, 'SELF_UPLOAD_IDENTITY_PHOTO', actor.code, photo.name)
        elif request.FILES.get('identity_photo'):
            messages.error(request, 'Ajout de photo bloqué par les paramètres RGPD de votre dossier.')
            log_core_action(actor, 'SELF_BLOCKED_PHOTO_UPLOAD', actor.code, 'blocked')
        actor.save()
        doc = request.FILES.get('document_file')
        if doc and not actor.personal_upload_blocked:
            CoreUserDocument.objects.create(user=actor, type_document=request.POST.get('type_document') or 'autre', title=request.POST.get('document_title') or doc.name, file=doc, uploaded_by=actor)
            log_core_action(actor, 'SELF_UPLOAD_DOCUMENT', actor.code, doc.name)
        elif doc:
            messages.error(request, 'Ajout de document bloqué par les paramètres RGPD de votre dossier.')
        messages.success(request, 'Compte personnel mis à jour.')
        return redirect('core_my_account')
    return render(request, 'core/my_account.html', {'target_user': actor, 'documents': actor.personal_documents.all(), 'document_types': CoreUserDocument.DOC_TYPE_CHOICES})


@require_http_methods(['GET', 'POST'])
def rgpd_center(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    policy = RgpdPolicySettings.get_solo()
    if request.method == 'POST':
        policy.technical_logs_retention = request.POST.get('technical_logs_retention') or policy.technical_logs_retention
        try:
            policy.backup_retention_days = int(request.POST.get('backup_retention_days') or policy.backup_retention_days)
        except ValueError:
            pass
        policy.certification_support_note = request.POST.get('certification_support_note') or policy.certification_support_note
        policy.photo_purpose = request.POST.get('photo_purpose') or policy.photo_purpose
        policy.minor_authorization_note = request.POST.get('minor_authorization_note') or policy.minor_authorization_note
        policy.save()
        messages.success(request, 'Paramètres RGPD mis à jour.')
        return redirect('core_rgpd')
    return render(request, 'core/rgpd.html', {'policy': policy, 'audit_logs': CoreAuditLog.objects.select_related('actor')[:100]})



def _public_settings_int(request, key, default):
    try:
        return int(request.POST.get(key) or default)
    except (TypeError, ValueError):
        return default




def _updates_base_dir():
    base = Path(getattr(settings, 'LP_CORE_UPDATES_DIR', os.getenv('LP_CORE_UPDATES_DIR', '/data/lp-core/updates')))
    (base / 'incoming').mkdir(parents=True, exist_ok=True)
    (base / 'logs').mkdir(parents=True, exist_ok=True)
    return base


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def _inspect_update_zip(path):
    """Analyse non destructive du ZIP de mise à jour.

    Refuse les chemins absolus, les remontées ../ et cherche un manifest.json.
    """
    report = []
    manifest = {}
    detected_version = ''
    with zipfile.ZipFile(path, 'r') as zf:
        names = zf.namelist()
        if not names:
            raise ValueError('Le ZIP est vide.')
        for name in names:
            clean = name.replace('\\', '/')
            if clean.startswith('/') or '..' in Path(clean).parts:
                raise ValueError(f'Chemin interdit dans le ZIP : {name}')
        report.append(f'{len(names)} entrée(s) dans le ZIP.')
        manifest_candidates = [n for n in names if n.endswith('manifest.json')]
        if manifest_candidates:
            with zf.open(manifest_candidates[0]) as f:
                manifest = json.loads(f.read().decode('utf-8'))
            detected_version = str(manifest.get('version') or manifest.get('suite_version') or '')
            report.append(f'Manifest détecté : {manifest_candidates[0]}')
            if detected_version:
                report.append(f'Version détectée : {detected_version}')
        else:
            report.append('Aucun manifest.json détecté. Installation possible mais moins contrôlée.')
        if not any(n.endswith('docker-compose.yml') for n in names):
            report.append('Attention : docker-compose.yml non détecté dans le ZIP.')
    return manifest, detected_version, '\n'.join(report)


def _call_admin_agent(action, payload=None, timeout=10):
    if not getattr(settings, 'SUITE_ALLOW_WEB_MAINTENANCE', True):
        return {'ok': False, 'error': 'Maintenance web désactivée par configuration serveur.'}
    payload = payload or {}
    url = getattr(settings, 'SUITE_ADMIN_AGENT_URL', 'http://suite-admin-agent:8079').rstrip('/') + '/actions'
    headers = {'X-Agent-Token': getattr(settings, 'LP_CORE_API_TOKEN', '') or ''}
    try:
        response = requests.post(url, json={'action': action, **payload}, headers=headers, timeout=timeout)
        try:
            data = response.json()
        except Exception:
            data = {'ok': response.ok, 'raw': response.text[:2000]}
        if not response.ok:
            data.setdefault('ok', False)
            data.setdefault('error', f'Agent HTTP {response.status_code}')
        return data
    except requests.RequestException as exc:
        return {'ok': False, 'error': f'Agent inaccessible : {exc}'}


def _refresh_agent_job(job):
    if not job.agent_job_id:
        return job
    url = getattr(settings, 'SUITE_ADMIN_AGENT_URL', 'http://suite-admin-agent:8079').rstrip('/') + f'/jobs/{job.agent_job_id}'
    headers = {'X-Agent-Token': getattr(settings, 'LP_CORE_API_TOKEN', '') or ''}
    try:
        response = requests.get(url, headers=headers, timeout=3)
        if response.ok:
            data = response.json()
            status = data.get('status') or job.status
            if status in {'queued', 'running'}:
                job.status = 'running'
            elif status in {'success', 'failed'}:
                job.status = status
            else:
                job.status = 'unknown'
            job.result_message = data.get('message', job.result_message) or ''
            job.log_tail = data.get('log_tail', job.log_tail) or ''
            job.save(update_fields=['status', 'result_message', 'log_tail', 'updated_at'])
    except requests.RequestException:
        pass
    return job


def _record_agent_job(action, actor, payload=None, package=None, success_message=None):
    data = _call_admin_agent(action, payload=payload or {})
    job = SuiteMaintenanceJob.objects.create(
        action=action,
        status='requested' if data.get('ok') else 'failed',
        agent_job_id=str(data.get('job_id') or ''),
        package=package,
        requested_by=actor,
        result_message=success_message or data.get('message') or data.get('error') or '',
    )
    if data.get('ok'):
        job.status = 'running'
        job.save(update_fields=['status', 'updated_at'])
    return job, data


def _cert_file_status(path_value):
    path = Path(path_value or '')
    status = {'path': str(path), 'exists': path.exists(), 'details': ''}
    if path.exists():
        try:
            status['details'] = f'{path.stat().st_size} octets'
        except Exception as exc:
            status['details'] = str(exc)
    return status


def _write_uploaded_cert(uploaded, target_path, *, private_key=False):
    target = Path(target_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, 'wb') as dst:
        for chunk in uploaded.chunks():
            dst.write(chunk)
    if private_key:
        try:
            os.chmod(target, 0o600)
        except Exception:
            pass
    return target

@require_http_methods(['GET', 'POST'])
def public_settings_view(request):
    """Configuration centralisée des URLs publiques, du protocole et du challenge TLS.

    La page écrit aussi un fichier /data/lp-core/cert-manager.env. Le script hôte
    scripts/apply_public_settings.sh peut ensuite injecter ces valeurs dans .env
    et scripts/cert_manager.sh peut générer/renouveler le certificat.
    """
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    settings_obj = PublicSuiteSettings.get_solo()
    cert_env_path = Path(settings.LP_CORE_DATA_DIR if hasattr(settings, 'LP_CORE_DATA_DIR') else os.getenv('LP_CORE_DATA_DIR', '/data/lp-core')) / 'cert-manager.env'
    # Fallback propre : settings.DATA_DIR existe dans settings.py mais n'est pas exporté comme nom Django public.
    cert_env_path = Path(os.getenv('LP_CORE_DATA_DIR', '/data/lp-core')) / 'cert-manager.env'
    if request.method == 'POST':
        selected_mode = request.POST.get('exposure_mode') or settings_obj.exposure_mode or 'local'
        if selected_mode not in {'local', 'network', 'domain'}:
            selected_mode = 'local'
        settings_obj.exposure_mode = selected_mode
        settings_obj.local_public_host = (request.POST.get('local_public_host') or settings_obj.local_public_host or 'localhost:9000').strip().replace('https://', '').replace('http://', '').strip('/')
        settings_obj.network_public_host = (request.POST.get('network_public_host') or settings_obj.network_public_host or '').strip().replace('https://', '').replace('http://', '').strip('/')
        settings_obj.external_public_domain = (request.POST.get('external_public_domain') or settings_obj.external_public_domain or '').strip().replace('https://', '').replace('http://', '').strip('/')
        legacy_domain = (request.POST.get('public_domain') or '').strip().replace('https://', '').replace('http://', '').strip('/')
        if legacy_domain and not settings_obj.external_public_domain:
            settings_obj.external_public_domain = legacy_domain
        settings_obj.public_scheme = request.POST.get('public_scheme') or ('https' if selected_mode == 'domain' else 'http')
        settings_obj.public_domain = settings_obj.selected_host()
        settings_obj.challenge_method = request.POST.get('challenge_method') or 'dns_duckdns'
        settings_obj.letsencrypt_email = (request.POST.get('letsencrypt_email') or '').strip()
        posted_token = (request.POST.get('duckdns_token') or '').strip()
        if posted_token:
            settings_obj.duckdns_token = posted_token
        settings_obj.enable_https = request.POST.get('enable_https') == '1'
        settings_obj.ssl_cert_file = request.POST.get('ssl_cert_file') or '/ssl/fullchain.pem'
        settings_obj.ssl_key_file = request.POST.get('ssl_key_file') or '/ssl/privkey.pem'
        cert_upload = request.FILES.get('certificate_file')
        key_upload = request.FILES.get('private_key_file')
        if cert_upload:
            _write_uploaded_cert(cert_upload, settings_obj.ssl_cert_file, private_key=False)
            messages.success(request, 'Certificat importé dans le volume SSL.')
        if key_upload:
            _write_uploaded_cert(key_upload, settings_obj.ssl_key_file, private_key=True)
            messages.success(request, 'Clé privée importée dans le volume SSL.')
        settings_obj.save()
        cert_env_path.parent.mkdir(parents=True, exist_ok=True)
        cert_env_path.write_text(settings_obj.to_env_text(), encoding='utf-8')
        messages.success(request, 'Paramètres publics enregistrés. Fichier cert-manager.env généré dans les données LP Core.')
        return redirect('core_public_settings')
    context = {
        'settings_obj': settings_obj,
        'module_urls': settings_obj.module_urls(),
        'csrf_origins': settings_obj.csrf_origins(),
        'cert_env_path': cert_env_path,
        'duckdns_token_configured': bool(settings_obj.duckdns_token),
        'cert_file_status': _cert_file_status(settings_obj.ssl_cert_file),
        'key_file_status': _cert_file_status(settings_obj.ssl_key_file),
    }
    return render(request, 'core/public_settings.html', context)

@require_http_methods(['POST'])
def public_settings_server_action(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    action = request.POST.get('server_action') or ''
    allowed = {
        'apply_public_settings': 'Application des paramètres publics demandée.',
        'issue_cert': 'Génération du certificat demandée.',
        'renew_cert': 'Renouvellement du certificat demandé.',
        'cert_status': 'Lecture de l’état certificat demandée.',
        'restart_services': 'Redémarrage des services demandé.',
    }
    if action not in allowed:
        messages.error(request, 'Action serveur inconnue ou non autorisée.')
        return redirect('core_public_settings')
    job, data = _record_agent_job(action, actor, success_message=allowed[action])
    if data.get('ok'):
        messages.success(request, f'{allowed[action]} Job agent : {job.agent_job_id or "non communiqué"}.')
    else:
        messages.error(request, job.result_message or 'L’agent serveur n’a pas accepté la demande.')
    return redirect('core_suite_updates')


@require_http_methods(['GET', 'POST'])
def suite_updates_view(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    base = _updates_base_dir()
    max_size = getattr(settings, 'MAX_UPDATE_ZIP_SIZE_MB', 500) * 1024 * 1024
    if request.method == 'POST':
        form_action = request.POST.get('form_action') or ''
        if form_action == 'upload_update':
            uploaded = request.FILES.get('update_zip')
            if not uploaded:
                messages.error(request, 'Aucun ZIP reçu.')
                return redirect('core_suite_updates')
            if not uploaded.name.lower().endswith('.zip'):
                messages.error(request, 'Le fichier doit être une archive .zip.')
                return redirect('core_suite_updates')
            if uploaded.size > max_size:
                messages.error(request, f'Le ZIP dépasse la taille maximale autorisée ({getattr(settings, "MAX_UPDATE_ZIP_SIZE_MB", 500)} Mo).')
                return redirect('core_suite_updates')
            safe_name = get_valid_filename(Path(uploaded.name).name)
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            stored_name = f'{stamp}-{safe_name}'
            stored_path = base / 'incoming' / stored_name
            with open(stored_path, 'wb') as dst:
                for chunk in uploaded.chunks():
                    dst.write(chunk)
            pkg = UploadedUpdatePackage.objects.create(
                original_filename=uploaded.name,
                stored_filename=stored_name,
                stored_path=str(stored_path),
                size_bytes=stored_path.stat().st_size,
                sha256=_sha256_file(stored_path),
                uploaded_by=actor,
                status='uploaded',
            )
            try:
                manifest, detected_version, report = _inspect_update_zip(stored_path)
                pkg.manifest = manifest
                pkg.detected_version = detected_version
                pkg.analysis_report = report
                pkg.status = 'analyzed'
                pkg.save()
                messages.success(request, f'ZIP reçu et analysé : {uploaded.name}.')
            except Exception as exc:
                pkg.status = 'invalid'
                pkg.analysis_report = str(exc)
                pkg.save()
                messages.error(request, f'ZIP refusé : {exc}')
            return redirect('core_suite_updates')

        if form_action == 'agent_action':
            action = request.POST.get('agent_action') or ''
            allowed = {'backup_all', 'migrate_all', 'restart_services'}
            if action not in allowed:
                messages.error(request, 'Action de maintenance inconnue ou non autorisée.')
                return redirect('core_suite_updates')
            job, data = _record_agent_job(action, actor)
            if data.get('ok'):
                messages.success(request, f'Action lancée : {job.get_action_display()} — job {job.agent_job_id}.')
            else:
                messages.error(request, job.result_message or 'Action refusée par l’agent serveur.')
            return redirect('core_suite_updates')

        if form_action == 'install_update':
            pkg = get_object_or_404(UploadedUpdatePackage, pk=request.POST.get('package_id'))
            if pkg.status not in {'analyzed', 'failed'}:
                messages.error(request, 'Ce paquet n’est pas installable dans son état actuel.')
                return redirect('core_suite_updates')
            pkg.status = 'installing'
            pkg.save(update_fields=['status', 'updated_at'])
            job, data = _record_agent_job('install_update', actor, payload={'filename': pkg.stored_filename}, package=pkg)
            if data.get('ok'):
                messages.success(request, f'Installation lancée pour {pkg.original_filename} — job {job.agent_job_id}.')
            else:
                pkg.status = 'failed'
                pkg.save(update_fields=['status', 'updated_at'])
                messages.error(request, job.result_message or 'Installation refusée par l’agent serveur.')
            return redirect('core_suite_updates')

        messages.error(request, 'Action inconnue.')
        return redirect('core_suite_updates')

    jobs = list(SuiteMaintenanceJob.objects.select_related('package', 'requested_by')[:12])
    for job in jobs:
        if job.status in {'requested', 'running'}:
            _refresh_agent_job(job)
            if job.action == 'install_update' and job.package:
                if job.status == 'success' and job.package.status != 'installed':
                    job.package.status = 'installed'
                    job.package.save(update_fields=['status', 'updated_at'])
                elif job.status == 'failed' and job.package.status != 'failed':
                    job.package.status = 'failed'
                    job.package.save(update_fields=['status', 'updated_at'])
    context = {
        'packages': UploadedUpdatePackage.objects.select_related('uploaded_by')[:20],
        'jobs': jobs,
        'updates_dir': base,
        'agent_url': getattr(settings, 'SUITE_ADMIN_AGENT_URL', 'http://suite-admin-agent:8079'),
        'web_maintenance_enabled': getattr(settings, 'SUITE_ALLOW_WEB_MAINTENANCE', True),
        'max_zip_mb': getattr(settings, 'MAX_UPDATE_ZIP_SIZE_MB', 500),
    }
    return render(request, 'core/suite_updates.html', context)




DATABASE_BACKUP_MODULES = [
    ('all', 'Toutes les bases'),
    ('lp-core', 'LP Core'),
    ('toolmag', 'ToolMag'),
    ('safety', 'Safety Manager'),
    ('pedashop', 'PedaShop'),
    ('system-manager', 'System Manager'),
    ('tpmanager', 'TP Manager'),
    ('pfmp', 'PFMP Manager'),
]
DATABASE_BACKUP_MODULE_CODES = {code for code, _label in DATABASE_BACKUP_MODULES}


def _inspect_database_backup_zip(path):
    report = []
    manifest = {}
    with zipfile.ZipFile(path, 'r') as zf:
        names = zf.namelist()
        if not names:
            raise ValueError('Le ZIP est vide.')
        for name in names:
            clean = name.replace('\\', '/')
            if clean.startswith('/') or '..' in Path(clean).parts:
                raise ValueError(f'Chemin interdit dans le ZIP : {name}')
        if 'manifest.json' not in names:
            raise ValueError('manifest.json absent. Sauvegarde base refusée.')
        with zf.open('manifest.json') as f:
            manifest = json.loads(f.read().decode('utf-8'))
        if manifest.get('package_type') != 'database_backup':
            raise ValueError('Le ZIP n’est pas déclaré comme sauvegarde base PostgreSQL.')
        dumps = [n for n in names if n.startswith('databases/') and n.endswith('.dump')]
        if not dumps:
            raise ValueError('Aucun dump PostgreSQL détecté dans databases/*.dump.')
        if 'checksums.sha256' in names:
            report.append('Checksums internes présents. Vérification détaillée effectuée par l’agent avant restauration.')
        report.append(f"Type : {manifest.get('backup_type', 'database_backup')}")
        report.append(f"Module déclaré : {manifest.get('module', 'auto')}")
        report.append(f"Dump(s) : {', '.join(Path(d).name for d in dumps)}")
    return manifest, '\n'.join(report)

def _inspect_full_backup_zip(path):
    """Analyse non destructive d'une sauvegarde complète LP Suite."""
    report = []
    manifest = {}
    with zipfile.ZipFile(path, 'r') as zf:
        names = zf.namelist()
        if not names:
            raise ValueError('La sauvegarde ZIP est vide.')
        for name in names:
            clean = name.replace('\\', '/')
            if clean.startswith('/') or '..' in Path(clean).parts:
                raise ValueError(f'Chemin interdit dans le ZIP : {name}')
        manifest_candidates = [n for n in names if n.endswith('manifest.json')]
        if not manifest_candidates:
            raise ValueError('manifest.json introuvable : ce ZIP n’est pas reconnu comme sauvegarde complète.')
        with zf.open(manifest_candidates[0]) as f:
            manifest = json.loads(f.read().decode('utf-8'))
        if manifest.get('suite') != 'lp-gestion-atelier-ep-suite':
            raise ValueError('La sauvegarde ne déclare pas la suite lp-gestion-atelier-ep-suite.')
        report.append(f"Manifest : {manifest_candidates[0]}")
        report.append(f"Type : {manifest.get('backup_type', 'inconnu')}")
        report.append(f"Créée le : {manifest.get('created_at', 'non renseigné')}")
        report.append(f"Hôte source : {manifest.get('hostname', 'non renseigné')}")
        expected = ['lp-core-db', 'toolmag-db', 'safety-db', 'pedashop-db', 'system-manager-db', 'tpmanager-db']
        present = []
        for prefix in expected:
            if any(n.startswith(prefix + '/') for n in names) or any(('/' + prefix + '/') in n for n in names):
                present.append(prefix)
        report.append('Bases détectées : ' + (', '.join(present) if present else 'aucune base détectée'))
        if 'checksums.sha256' in [Path(n).name for n in names]:
            report.append('Contrôles SHA-256 présents.')
        else:
            report.append('Avertissement : checksums.sha256 absent.')
    return manifest, '\n'.join(report)



def _backup_policy_env_path():
    return Path(os.getenv('LP_CORE_DATA_DIR', '/data/lp-core')) / 'backup-policy.env'


def _write_backup_policy_env(policy):
    path = _backup_policy_env_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(policy.to_env_text(), encoding='utf-8')
    return path


def _agent_get(path, timeout=5):
    url = getattr(settings, 'SUITE_ADMIN_AGENT_URL', 'http://suite-admin-agent:8079').rstrip('/') + path
    headers = {'X-Agent-Token': getattr(settings, 'LP_CORE_API_TOKEN', '') or ''}
    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        try:
            data = response.json()
        except Exception:
            data = {'ok': response.ok, 'raw': response.text[:2000]}
        if not response.ok:
            data.setdefault('ok', False)
            data.setdefault('error', f'Agent HTTP {response.status_code}')
        return data
    except requests.RequestException as exc:
        return {'ok': False, 'error': f'Agent inaccessible : {exc}'}

@require_http_methods(['GET', 'POST'])
def backup_restore_view(request):
    """Centre de sauvegarde / restauration complète après crash serveur.

    Cette page pilote aussi la politique de sauvegarde : heure, durée de
    conservation, obligation de sauvegarde pré-mise-à-jour et restauration web.
    """
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    base = _updates_base_dir()
    max_size = getattr(settings, 'MAX_UPDATE_ZIP_SIZE_MB', 500) * 1024 * 1024
    policy = BackupPolicySettings.get_solo()
    # Maintient le centre RGPD cohérent avec la durée réelle de rotation.
    rgpd_policy = RgpdPolicySettings.get_solo()

    if request.method == 'POST':
        form_action = request.POST.get('form_action') or ''
        if form_action == 'save_backup_settings':
            try:
                policy.automatic_enabled = request.POST.get('automatic_enabled') == '1'
                policy.daily_hour = int(request.POST.get('daily_hour') or policy.daily_hour)
                policy.daily_minute = int(request.POST.get('daily_minute') or policy.daily_minute)
                policy.daily_retention_days = int(request.POST.get('daily_retention_days') or policy.daily_retention_days)
                policy.manual_keep_forever = request.POST.get('manual_keep_forever') == '1'
                policy.pre_upgrade_required = request.POST.get('pre_upgrade_required') == '1'
                policy.block_update_if_backup_failed = request.POST.get('block_update_if_backup_failed') == '1'
                policy.web_restore_enabled = request.POST.get('web_restore_enabled') == '1'
                policy.notes = request.POST.get('notes') or ''
                policy.save()
                rgpd_policy.backup_retention_days = policy.daily_retention_days
                rgpd_policy.save(update_fields=['backup_retention_days', 'updated_at'])
                env_path = _write_backup_policy_env(policy)
                messages.success(request, f'Paramètres de sauvegarde enregistrés. Fichier généré : {env_path}.')
                log_core_action(actor, 'BACKUP_SETTINGS_UPDATED', 'backup-policy', policy.to_env_text())
            except Exception as exc:
                messages.error(request, f'Paramètres non enregistrés : {exc}')
            return redirect('core_backup_restore')

        if form_action == 'full_backup':
            job, data = _record_agent_job('full_backup', actor)
            if data.get('ok'):
                messages.success(request, f'Sauvegarde complète lancée — job {job.agent_job_id}.')
            else:
                messages.error(request, job.result_message or 'Sauvegarde refusée par l’agent serveur.')
            return redirect('core_backup_restore')


        if form_action == 'backup_database':
            module = request.POST.get('database_module') or 'all'
            if module not in DATABASE_BACKUP_MODULE_CODES:
                messages.error(request, 'Module de sauvegarde base non autorisé.')
                return redirect('core_backup_restore')
            job, data = _record_agent_job('backup_database', actor, payload={'module': module})
            if data.get('ok'):
                messages.success(request, f'Sauvegarde base lancée pour {module} — job {job.agent_job_id}.')
            else:
                messages.error(request, job.result_message or 'Sauvegarde base refusée par l’agent serveur.')
            return redirect('core_backup_restore')

        if form_action == 'upload_db_restore':
            if not policy.web_restore_enabled:
                messages.error(request, 'La restauration depuis l’interface web est désactivée dans les paramètres sauvegarde.')
                return redirect('core_backup_restore')
            uploaded = request.FILES.get('database_backup_zip')
            if not uploaded:
                messages.error(request, 'Aucune sauvegarde base ZIP reçue.')
                return redirect('core_backup_restore')
            if not uploaded.name.lower().endswith('.zip'):
                messages.error(request, 'La sauvegarde base doit être une archive .zip.')
                return redirect('core_backup_restore')
            if uploaded.size > max_size:
                messages.error(request, f'Le ZIP dépasse la taille maximale autorisée ({getattr(settings, "MAX_UPDATE_ZIP_SIZE_MB", 500)} Mo).')
                return redirect('core_backup_restore')
            safe_name = get_valid_filename(Path(uploaded.name).name)
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            stored_name = f'db-restore-{stamp}-{safe_name}'
            stored_path = base / 'incoming' / stored_name
            with open(stored_path, 'wb') as dst:
                for chunk in uploaded.chunks():
                    dst.write(chunk)
            pkg = UploadedUpdatePackage.objects.create(original_filename=uploaded.name, stored_filename=stored_name, stored_path=str(stored_path), size_bytes=stored_path.stat().st_size, sha256=_sha256_file(stored_path), uploaded_by=actor, status='uploaded')
            try:
                manifest, report = _inspect_database_backup_zip(stored_path)
                pkg.manifest = manifest
                pkg.detected_version = str(manifest.get('source_version') or manifest.get('created_at') or '')
                pkg.analysis_report = report
                pkg.status = 'analyzed'
                pkg.save()
                messages.success(request, 'Sauvegarde base reçue et analysée. Vérifie le rapport avant restauration.')
            except Exception as exc:
                pkg.status = 'invalid'
                pkg.analysis_report = str(exc)
                pkg.save()
                messages.error(request, f'Sauvegarde base refusée : {exc}')
            return redirect('core_backup_restore')

        if form_action == 'restore_database_backup':
            if not policy.web_restore_enabled:
                messages.error(request, 'La restauration depuis l’interface web est désactivée dans les paramètres sauvegarde.')
                return redirect('core_backup_restore')
            pkg = get_object_or_404(UploadedUpdatePackage, pk=request.POST.get('package_id'))
            module = request.POST.get('database_restore_module') or 'auto'
            if module != 'auto' and module not in DATABASE_BACKUP_MODULE_CODES:
                messages.error(request, 'Module de restauration base non autorisé.')
                return redirect('core_backup_restore')
            confirm = (request.POST.get('confirm_restore_database') or '').strip().upper()
            if confirm != 'RESTAURER':
                messages.error(request, 'Confirmation incorrecte. Saisir RESTAURER pour lancer la restauration base.')
                return redirect('core_backup_restore')
            job, data = _record_agent_job('restore_database_backup', actor, payload={'filename': pkg.stored_filename, 'module': module}, package=pkg)
            if data.get('ok'):
                messages.success(request, f'Restauration base lancée — job {job.agent_job_id}.')
            else:
                messages.error(request, job.result_message or 'Restauration base refusée par l’agent serveur.')
            return redirect('core_backup_restore')

        if form_action == 'restore_existing_database_backup':
            if not policy.web_restore_enabled:
                messages.error(request, 'La restauration depuis l’interface web est désactivée dans les paramètres sauvegarde.')
                return redirect('core_backup_restore')
            backup_path = request.POST.get('database_backup_path') or ''
            module = request.POST.get('database_restore_module') or 'auto'
            if module != 'auto' and module not in DATABASE_BACKUP_MODULE_CODES:
                messages.error(request, 'Module de restauration base non autorisé.')
                return redirect('core_backup_restore')
            confirm = (request.POST.get('confirm_restore_existing_database') or '').strip().upper()
            if confirm != 'RESTAURER':
                messages.error(request, 'Confirmation incorrecte. Saisir RESTAURER pour restaurer une sauvegarde base serveur.')
                return redirect('core_backup_restore')
            job, data = _record_agent_job('restore_database_backup', actor, payload={'backup_path': backup_path, 'module': module})
            if data.get('ok'):
                messages.success(request, f'Restauration base serveur lancée — job {job.agent_job_id}.')
            else:
                messages.error(request, job.result_message or 'Restauration base serveur refusée par l’agent.')
            return redirect('core_backup_restore')

        if form_action == 'upload_restore':
            if not policy.web_restore_enabled:
                messages.error(request, 'La restauration depuis l’interface web est désactivée dans les paramètres sauvegarde.')
                return redirect('core_backup_restore')
            uploaded = request.FILES.get('backup_zip')
            if not uploaded:
                messages.error(request, 'Aucune sauvegarde ZIP reçue.')
                return redirect('core_backup_restore')
            if not uploaded.name.lower().endswith('.zip'):
                messages.error(request, 'La sauvegarde doit être une archive .zip.')
                return redirect('core_backup_restore')
            if uploaded.size > max_size:
                messages.error(request, f'Le ZIP dépasse la taille maximale autorisée ({getattr(settings, "MAX_UPDATE_ZIP_SIZE_MB", 500)} Mo).')
                return redirect('core_backup_restore')
            safe_name = get_valid_filename(Path(uploaded.name).name)
            stamp = datetime.now().strftime('%Y%m%d-%H%M%S')
            stored_name = f'restore-{stamp}-{safe_name}'
            stored_path = base / 'incoming' / stored_name
            with open(stored_path, 'wb') as dst:
                for chunk in uploaded.chunks():
                    dst.write(chunk)
            pkg = UploadedUpdatePackage.objects.create(
                original_filename=uploaded.name,
                stored_filename=stored_name,
                stored_path=str(stored_path),
                size_bytes=stored_path.stat().st_size,
                sha256=_sha256_file(stored_path),
                uploaded_by=actor,
                status='uploaded',
            )
            try:
                manifest, report = _inspect_full_backup_zip(stored_path)
                pkg.manifest = manifest
                pkg.detected_version = str(manifest.get('source_version') or manifest.get('created_at') or '')
                pkg.analysis_report = report
                pkg.status = 'analyzed'
                pkg.save()
                messages.success(request, 'Sauvegarde reçue et analysée. Vérifie le rapport avant restauration.')
            except Exception as exc:
                pkg.status = 'invalid'
                pkg.analysis_report = str(exc)
                pkg.save()
                messages.error(request, f'Sauvegarde refusée : {exc}')
            return redirect('core_backup_restore')

        if form_action == 'restore_full_backup':
            if not policy.web_restore_enabled:
                messages.error(request, 'La restauration depuis l’interface web est désactivée dans les paramètres sauvegarde.')
                return redirect('core_backup_restore')
            pkg = get_object_or_404(UploadedUpdatePackage, pk=request.POST.get('package_id'))
            if pkg.status != 'analyzed':
                messages.error(request, 'Cette sauvegarde n’est pas restaurable dans son état actuel.')
                return redirect('core_backup_restore')
            confirm = (request.POST.get('confirm_restore') or '').strip().upper()
            if confirm != 'RESTAURER':
                messages.error(request, 'Confirmation incorrecte. Saisir RESTAURER pour lancer une reprise complète.')
                return redirect('core_backup_restore')
            job, data = _record_agent_job('restore_full_backup', actor, payload={'filename': pkg.stored_filename}, package=pkg)
            if data.get('ok'):
                messages.success(request, f'Restauration complète lancée — job {job.agent_job_id}. LP Core peut redémarrer pendant l’opération.')
            else:
                messages.error(request, job.result_message or 'Restauration refusée par l’agent serveur.')
            return redirect('core_backup_restore')

        if form_action == 'restore_existing_backup':
            if not policy.web_restore_enabled:
                messages.error(request, 'La restauration depuis l’interface web est désactivée dans les paramètres sauvegarde.')
                return redirect('core_backup_restore')
            backup_path = request.POST.get('backup_path') or ''
            confirm = (request.POST.get('confirm_restore_existing') or '').strip().upper()
            if confirm != 'RESTAURER':
                messages.error(request, 'Confirmation incorrecte. Saisir RESTAURER pour restaurer une sauvegarde serveur.')
                return redirect('core_backup_restore')
            job, data = _record_agent_job('restore_existing_backup', actor, payload={'backup_path': backup_path})
            if data.get('ok'):
                messages.success(request, f'Restauration serveur lancée — job {job.agent_job_id}.')
            else:
                messages.error(request, job.result_message or 'Restauration serveur refusée par l’agent.')
            return redirect('core_backup_restore')

        messages.error(request, 'Action inconnue.')
        return redirect('core_backup_restore')

    jobs = list(SuiteMaintenanceJob.objects.select_related('package', 'requested_by').filter(action__in=['full_backup', 'restore_full_backup', 'restore_existing_backup', 'backup_all', 'backup_database', 'restore_database_backup'])[:12])
    for job in jobs:
        if job.status in {'requested', 'running'}:
            _refresh_agent_job(job)
    packages = UploadedUpdatePackage.objects.select_related('uploaded_by').filter(original_filename__iendswith='.zip')[:20]
    existing_backups_response = _agent_get('/backups')
    existing_backups = existing_backups_response.get('backups', []) if existing_backups_response.get('ok') else []
    database_backups_response = _agent_get('/database-backups')
    database_backups = database_backups_response.get('backups', []) if database_backups_response.get('ok') else []
    context = {
        'jobs': jobs,
        'packages': packages,
        'existing_backups': existing_backups,
        'existing_backups_error': '' if existing_backups_response.get('ok') else existing_backups_response.get('error', 'Liste indisponible'),
        'database_backups': database_backups,
        'database_backups_error': '' if database_backups_response.get('ok') else database_backups_response.get('error', 'Liste indisponible'),
        'database_backup_modules': DATABASE_BACKUP_MODULES,
        'updates_dir': base,
        'agent_url': getattr(settings, 'SUITE_ADMIN_AGENT_URL', 'http://suite-admin-agent:8079'),
        'max_zip_mb': getattr(settings, 'MAX_UPDATE_ZIP_SIZE_MB', 500),
        'backup_policy': policy,
        'backup_policy_env_path': _backup_policy_env_path(),
        'backup_retention_days': policy.daily_retention_days,
        'backup_daily_hour': f'{int(policy.daily_hour):02d}',
        'backup_daily_minute': f'{int(policy.daily_minute):02d}',
    }
    return render(request, 'core/backup_restore.html', context)


# --- Supervision PostgreSQL LP Suite ---

def database_supervision_view(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    if not _core_sql_admin_user(request):
        messages.error(request, 'Accès réservé administrateur LP Core.')
        return redirect('core_login')
    from .db_supervision import collect_database_supervision
    context = collect_database_supervision()
    return render(request, 'core/database_supervision.html', context)

# --- Administration SQL base module ---
def _core_sql_admin_user(request):
    from .models import CoreUser
    uid = request.session.get('core_user_id')
    user = CoreUser.objects.filter(id=uid, active=True).first() if uid else None
    return user if user and user.is_admin_like else None


def sql_database_admin(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from .db_sql_admin import render_sql_admin
    if not _core_sql_admin_user(request):
        messages.error(request, 'Accès réservé administrateur LP Core.')
        return redirect('core_login')
    return render_sql_admin(request, 'core/sql_database.html', 'LP Core')


def sql_database_export(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from .db_sql_admin import export_sql_response
    if not _core_sql_admin_user(request):
        messages.error(request, 'Accès réservé administrateur LP Core.')
        return redirect('core_login')
    return export_sql_response(request, 'lp-core')


def sql_database_import(request):
    from django.contrib import messages
    from django.shortcuts import redirect
    from .db_sql_admin import import_sql_response
    if not _core_sql_admin_user(request):
        messages.error(request, 'Accès réservé administrateur LP Core.')
        return redirect('core_login')
    return import_sql_response(request, 'core/sql_database.html', 'LP Core', 'lp-core')

def help_view(request):
    return render(request, 'core/help.html')


def about_view(request):
    return render(request, 'core/about.html')


# ---------------------------------------------------------------------------
# V0.3.5 — Classes LP Core administrables pour les blocs atelier
# ---------------------------------------------------------------------------

@require_http_methods(['GET', 'POST'])
def core_classes(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    if request.method == 'POST':
        action = request.POST.get('form_action') or ''
        if action == 'class':
            pk = request.POST.get('class_id') or None
            obj = get_object_or_404(CoreClass, pk=pk) if pk else CoreClass()
            obj.name = (request.POST.get('name') or '').strip()
            obj.formation = CoreFormation.objects.filter(pk=request.POST.get('formation_id')).first() if request.POST.get('formation_id') else None
            obj.school_year = (request.POST.get('school_year') or '').strip()
            obj.active = request.POST.get('active', '0') == '1'
            obj.full_clean()
            obj.save()
            messages.success(request, f"Classe enregistrée : {obj.name}.")
        elif action == 'delete_classes':
            ids = request.POST.getlist('selected_classes')
            count = CoreClass.objects.filter(pk__in=ids).delete()[0]
            messages.success(request, f'{count} classe(s) supprimée(s).')
        return redirect('core_classes')
    edit_class = CoreClass.objects.filter(pk=request.GET.get('edit')).first() if request.GET.get('edit') else None
    return render(request, 'core/classes.html', {
        'classes': CoreClass.objects.select_related('formation').all().order_by('name', 'school_year'),
        'formations': CoreFormation.objects.filter(active=True).order_by('code'),
        'edit_class': edit_class,
    })

# ---------------------------------------------------------------------------
# V0.3.3 — Blocs atelier LP Core, communs à Sequence Manager/System Manager
# ---------------------------------------------------------------------------

@require_http_methods(['GET', 'POST'])
def atelier_blocks(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    if request.method == 'POST':
        action = request.POST.get('form_action') or 'block'
        if action == 'block':
            pk = request.POST.get('block_id') or None
            code = request.POST.get('code') or request.POST.get('name') or ''
            name = request.POST.get('name') or code
            block = get_object_or_404(CoreAtelierBlock, pk=pk) if pk else None
            created = False
            if block is None:
                block, created = CoreAtelierBlock.objects.get_or_create(code=normalize_code(code or name, 'BLOC_ATELIER', 80), defaults={'name': name})
            block.code = normalize_code(code or name, 'BLOC_ATELIER', 80)
            block.name = name
            block.description = request.POST.get('description') or ''
            block.active = request.POST.get('active', '0') == '1'
            block.full_clean()
            block.save()
            selected_classes = CoreClass.objects.filter(pk__in=request.POST.getlist('classes'))
            block.classes.set(selected_classes)
            # Compatibilité technique : les formations sont déduites, mais l'écran admin manipule uniquement les classes.
            block.formations.set(CoreFormation.objects.filter(classes__in=selected_classes).distinct())
            messages.success(request, f"Bloc atelier {'créé' if created else 'mis à jour'} : {block.code}.")
        elif action == 'slot':
            pk = request.POST.get('slot_id') or None
            slot = get_object_or_404(CoreAtelierBlockSlot, pk=pk) if pk else None
            if slot is None:
                block = get_object_or_404(CoreAtelierBlock, pk=request.POST.get('block_id'))
                slot = CoreAtelierBlockSlot(block=block)
            else:
                slot.block = get_object_or_404(CoreAtelierBlock, pk=request.POST.get('block_id'))
            slot.day_of_week = int(request.POST.get('day_of_week'))
            slot.label = request.POST.get('label') or ''
            slot.start_time = request.POST.get('start_time')
            slot.end_time = request.POST.get('end_time')
            slot.active = request.POST.get('active', '0') == '1'
            slot.full_clean()
            slot.save()
            messages.success(request, f"Créneau enregistré : {slot}.")
        elif action == 'delete_blocks':
            count = CoreAtelierBlock.objects.filter(pk__in=request.POST.getlist('selected_blocks')).delete()[0]
            messages.success(request, f'{count} bloc(s) supprimé(s).')
        elif action == 'delete_slots':
            count = CoreAtelierBlockSlot.objects.filter(pk__in=request.POST.getlist('selected_slots')).delete()[0]
            messages.success(request, f'{count} créneau(x) supprimé(s).')
        return redirect('core_atelier_blocks')
    edit_block = CoreAtelierBlock.objects.filter(pk=request.GET.get('edit_block')).first() if request.GET.get('edit_block') else None
    edit_slot = CoreAtelierBlockSlot.objects.select_related('block').filter(pk=request.GET.get('edit_slot')).first() if request.GET.get('edit_slot') else None
    return render(request, 'core/atelier_blocks.html', {
        'blocks': CoreAtelierBlock.objects.prefetch_related('classes', 'slots').all(),
        'classes': CoreClass.objects.filter(active=True).order_by('name', 'school_year'),
        'day_choices': CoreAtelierBlockSlot.DAY_CHOICES,
        'edit_block': edit_block,
        'edit_slot': edit_slot,
    })


@require_http_methods(['GET', 'POST'])
def core_workshop_zones(request):
    actor = require_core_admin(request)
    if not actor:
        return redirect('core_login')
    if request.method == 'POST':
        action = request.POST.get('form_action') or ''
        if action == 'zone':
            code = request.POST.get('code') or request.POST.get('name') or ''
            name = request.POST.get('name') or code
            obj, created = CoreWorkshopZone.objects.get_or_create(code=normalize_code(code or name, 'ZONE'), defaults={'name': name})
            obj.name = name
            obj.description = request.POST.get('description') or ''
            obj.order = int(request.POST.get('order') or obj.order or 100)
            obj.active = request.POST.get('active', '1') == '1'
            obj.save()
            messages.success(request, f"Zone atelier {'créée' if created else 'mise à jour'} : {obj.code}.")
        elif action == 'subzone':
            zone = get_object_or_404(CoreWorkshopZone, pk=request.POST.get('zone_id'))
            code = request.POST.get('code') or request.POST.get('name') or ''
            name = request.POST.get('name') or code
            obj, created = CoreWorkshopSubZone.objects.get_or_create(zone=zone, code=normalize_code(code or name, 'SOUS_ZONE'), defaults={'name': name})
            obj.name = name
            obj.description = request.POST.get('description') or ''
            obj.order = int(request.POST.get('order') or obj.order or 100)
            obj.active = request.POST.get('active', '1') == '1'
            obj.save()
            messages.success(request, f"Sous-zone {'créée' if created else 'mise à jour'} : {obj.code}.")
        elif action == 'delete_zones':
            ids = request.POST.getlist('selected_zones')
            count = CoreWorkshopZone.objects.filter(pk__in=ids).delete()[0]
            messages.success(request, f'{count} objet(s) supprimé(s).')
        elif action == 'delete_subzones':
            ids = request.POST.getlist('selected_subzones')
            count = CoreWorkshopSubZone.objects.filter(pk__in=ids).delete()[0]
            messages.success(request, f'{count} objet(s) supprimé(s).')
        return redirect('core_workshop_zones')
    return render(request, 'core/workshop_zones.html', {
        'zones': CoreWorkshopZone.objects.prefetch_related('subzones').all(),
        'subzones': CoreWorkshopSubZone.objects.select_related('zone').all(),
    })


def api_workshop_zones(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    zones = CoreWorkshopZone.objects.prefetch_related('subzones').filter(active=True).order_by('order', 'code')
    return JsonResponse({'results': [{
        'id': z.id,
        'code': z.code,
        'name': z.name,
        'description': z.description,
        'active': z.active,
        'order': z.order,
        'subzones': [{
            'id': sz.id,
            'code': sz.code,
            'name': sz.name,
            'description': sz.description,
            'active': sz.active,
            'order': sz.order,
        } for sz in z.subzones.filter(active=True).order_by('order', 'code')]
    } for z in zones]})


def api_atelier_blocks(request):
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    blocks = CoreAtelierBlock.objects.prefetch_related('classes', 'classes__formation', 'formations', 'slots').filter(active=True).order_by('code')
    return JsonResponse({'results': [{
        'id': b.id,
        'code': b.code,
        'name': b.name,
        'description': b.description,
        'active': b.active,
        'formation_codes': sorted(set([c.formation.code for c in b.classes.all() if c.formation] or [f.code for f in b.formations.all()])),
        'class_names': [c.name for c in b.classes.all()],
        'class_ids': [c.id for c in b.classes.all()],
        'niveau_codes': [],
        'slots': [{
            'id': s.id,
            'day_of_week': s.day_of_week,
            'day_label': s.get_day_of_week_display(),
            'label': s.label,
            'start_time': s.start_time.strftime('%H:%M:%S'),
            'end_time': s.end_time.strftime('%H:%M:%S'),
            'active': s.active,
        } for s in b.slots.filter(active=True)]
    } for b in blocks]})


@require_http_methods(['POST'])
def api_system_manager_referentials_import(request):
    """Import contrôlé des zones/sous-zones/blocs envoyés par System Manager."""
    if not api_allowed(request):
        return HttpResponseForbidden('API token invalide')
    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except Exception as exc:
        return JsonResponse({'error': f'JSON invalide : {exc}'}, status=400)
    report = {'zones_created': 0, 'zones_updated': 0, 'subzones_created': 0, 'subzones_updated': 0, 'blocks_created': 0, 'blocks_updated': 0, 'slots_created': 0, 'slots_updated': 0, 'errors': []}
    for item in payload.get('zones', []) or []:
        try:
            code = normalize_code(item.get('code') or item.get('name') or 'ZONE')
            zone, created = CoreWorkshopZone.objects.get_or_create(code=code, defaults={'name': item.get('name') or code})
            zone.name = item.get('name') or zone.name
            zone.description = item.get('description') or ''
            zone.order = int(item.get('order') or zone.order or 100)
            zone.active = bool(item.get('active', True))
            zone.save()
            report['zones_created' if created else 'zones_updated'] += 1
            for child in item.get('subzones', []) or []:
                scode = normalize_code(child.get('code') or child.get('name') or 'SOUS_ZONE')
                sub, sub_created = CoreWorkshopSubZone.objects.get_or_create(zone=zone, code=scode, defaults={'name': child.get('name') or scode})
                sub.name = child.get('name') or sub.name
                sub.description = child.get('description') or ''
                sub.order = int(child.get('order') or sub.order or 100)
                sub.active = bool(child.get('active', True))
                sub.save()
                report['subzones_created' if sub_created else 'subzones_updated'] += 1
        except Exception as exc:
            report['errors'].append(f"Zone {item.get('code') or item.get('name')}: {exc}")
    for item in payload.get('blocks', []) or []:
        try:
            code = normalize_code(item.get('code') or item.get('name') or 'BLOC_ATELIER', 'BLOC_ATELIER', 80)
            block, created = CoreAtelierBlock.objects.get_or_create(code=code, defaults={'name': item.get('name') or code})
            block.name = item.get('name') or block.name
            block.description = item.get('description') or ''
            block.active = bool(item.get('active', True))
            block.save()
            block.classes.clear()
            for cname in item.get('class_names', []) or []:
                c = CoreClass.objects.filter(name=cname).order_by('-active', 'id').first()
                if c:
                    block.classes.add(c)
            report['blocks_created' if created else 'blocks_updated'] += 1
            for slot in item.get('slots', []) or []:
                try:
                    start = datetime.strptime(str(slot.get('start_time'))[:5], '%H:%M').time()
                    end = datetime.strptime(str(slot.get('end_time'))[:5], '%H:%M').time()
                    sobj, screated = CoreAtelierBlockSlot.objects.get_or_create(
                        block=block,
                        day_of_week=int(slot.get('day_of_week')),
                        start_time=start,
                        end_time=end,
                        defaults={'label': slot.get('label') or '', 'active': bool(slot.get('active', True))},
                    )
                    sobj.label = slot.get('label') or sobj.label
                    sobj.active = bool(slot.get('active', True))
                    sobj.save()
                    report['slots_created' if screated else 'slots_updated'] += 1
                except Exception as exc:
                    report['errors'].append(f"Créneau {code}: {exc}")
        except Exception as exc:
            report['errors'].append(f"Bloc {item.get('code') or item.get('name')}: {exc}")
    return JsonResponse(report)
