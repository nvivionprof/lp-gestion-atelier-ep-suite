from __future__ import annotations
from django.conf import settings
from django.utils import timezone
import requests
from .models import TpUser, Formation, SystemePedagogiqueRef


def _headers():
    return {'X-API-Key': settings.LP_CORE_API_TOKEN} if settings.LP_CORE_API_TOKEN else {}


def sync_users_from_lp_core(timeout=90, force_password=False, core_user_id=None):
    api_url = settings.LP_CORE_API_URL.rstrip('/')
    url = f'{api_url}/api/users/{core_user_id}/' if core_user_id else f'{api_url}/api/users/'
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    data = [payload] if core_user_id else payload.get('results', [])
    report = {'created': 0, 'updated': 0, 'formations_created': 0, 'formations_updated': 0, 'errors': []}
    now = timezone.now()
    for item in data:
        try:
            formation_code = item.get('formation_code') or ''
            formation_name = item.get('formation_name') or formation_code
            if formation_code:
                formation, f_created = Formation.objects.get_or_create(code=formation_code, defaults={'nom': formation_name or formation_code})
                formation.nom = formation_name or formation.code
                formation.active = True
                formation.save()
                report['formations_created' if f_created else 'formations_updated'] += 1

            core_id = item.get('id')
            code = item.get('code') or item.get('username')
            username = item.get('username') or code

            # Idempotence renforcée : les versions précédentes pouvaient créer un
            # utilisateur par seed locale, puis essayer d'en créer un second par
            # core_user_id avec le même code. On rapproche maintenant l'existant.
            obj = None
            if core_id is not None:
                obj = TpUser.objects.filter(core_user_id=core_id).first()
            if obj is None and code:
                obj = TpUser.objects.filter(code=code).first()
            if obj is None and username:
                obj = TpUser.objects.filter(username=username).first()

            created = False
            if obj is None:
                obj = TpUser(core_user_id=core_id, code=code, username=username)
                created = True
            elif core_id is not None and not obj.core_user_id:
                obj.core_user_id = core_id

            obj.code = code
            obj.username = username
            obj.first_name = item.get('first_name') or ''
            obj.last_name = item.get('last_name') or ''
            obj.email = item.get('email') or ''
            obj.formation_code = formation_code
            obj.formation_name = formation_name or ''
            obj.class_name = item.get('class_name') or ''
            obj.group_name = item.get('group_name') or ''
            obj.role_principal = item.get('role_principal') or 'utilisateur'
            obj.rights = item.get('rights') or ''
            obj.active = bool(item.get('active', True))
            obj.school_year = item.get('school_year') or ''
            obj.synced_at = now
            initial_password = item.get('initial_password') or ''
            if initial_password and (created or force_password or settings.TPMANAGER_RESET_PASSWORDS_ON_SYNC):
                obj.set_password(initial_password)
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('username') or item.get('code')}: {exc}")
    return report

def sync_formations_from_lp_core(timeout=90):
    url = settings.LP_CORE_API_URL.rstrip('/') + '/api/formations/'
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    data = response.json().get('results', [])
    report = {'created': 0, 'updated': 0, 'errors': []}
    for item in data:
        try:
            core_id = item.get('id')
            code = item.get('code') or item.get('name') or f'CORE_{core_id or "FORMATION"}'
            nom = item.get('name') or item.get('code') or code

            # Idempotence renforcée : les premières versions synchronisaient parfois
            # les formations par code avant que core_formation_id soit connu.
            # On cherche donc d'abord par ID Core, puis par code, pour éviter les
            # erreurs UNIQUE constraint failed sur Formation.code.
            obj = None
            if core_id is not None:
                obj = Formation.objects.filter(core_formation_id=core_id).first()
            if obj is None:
                obj = Formation.objects.filter(code=code).first()

            created = False
            if obj is None:
                obj = Formation(core_formation_id=core_id, code=code, nom=nom)
                created = True
            elif core_id is not None and not obj.core_formation_id:
                obj.core_formation_id = core_id

            obj.code = code
            obj.nom = nom
            obj.active = bool(item.get('active', True))
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('code')}: {exc}")
    return report


def sync_systems_from_system_manager(timeout=30):
    base = settings.SYSTEM_MANAGER_API_URL.rstrip('/')
    # En interne Docker, l'application doit normalement être appelée sans le préfixe
    # public /system. On sécurise toutefois les deux cas pour éviter les 404 en
    # installation neuve lorsque APP_URL_PREFIX est actif.
    internal_base = base[:-len('/system')] if base.endswith('/system') else base
    candidates = [f'{internal_base}/api/systems/', f'{internal_base}/system/api/systems/']

    response = None
    last_error = None
    for url in candidates:
        try:
            response = requests.get(url, headers=_headers(), timeout=timeout, allow_redirects=False)
            if response.status_code in {301, 302, 303, 307, 308}:
                last_error = f'{url} redirige vers {response.headers.get("Location", "destination inconnue")}'
                continue
            response.raise_for_status()
            break
        except requests.RequestException as exc:
            last_error = str(exc)
            response = None
    else:
        return {'created': 0, 'updated': 0, 'errors': [f'API System Manager indisponible : {last_error or "aucune réponse"}']}

    data = response.json().get('results', [])
    report = {'created': 0, 'updated': 0, 'errors': []}
    now = timezone.now()
    for item in data:
        try:
            code = item.get('code') or str(item.get('id'))
            obj = None
            if item.get('id') is not None:
                obj = SystemePedagogiqueRef.objects.filter(system_manager_id=item.get('id')).first()
            if obj is None:
                obj = SystemePedagogiqueRef.objects.filter(code=code).first()
            created = False
            if obj is None:
                obj = SystemePedagogiqueRef(system_manager_id=item.get('id'), code=code, designation=item.get('designation') or code)
                created = True
            elif item.get('id') is not None and not obj.system_manager_id:
                obj.system_manager_id = item.get('id')
            obj.code = code
            obj.designation = item.get('designation') or code
            obj.zone_code = item.get('zone_code') or ''
            obj.zone_nom = item.get('zone_nom') or ''
            obj.statut = item.get('statut') or ''
            obj.actif = bool(item.get('actif', True))
            obj.synced_at = now
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('code')}: {exc}")
    return report
