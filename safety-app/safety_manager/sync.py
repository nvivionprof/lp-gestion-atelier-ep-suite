from __future__ import annotations
from django.conf import settings
from django.utils import timezone
import requests
from .models import SafetyUser


def sync_users_from_lp_core(timeout=90, force_password=False, core_user_id=None):
    api_url = settings.LP_CORE_API_URL.rstrip('/')
    url = f'{api_url}/api/users/{core_user_id}/' if core_user_id else f'{api_url}/api/users/'
    headers = {'X-API-Key': settings.LP_CORE_API_TOKEN} if settings.LP_CORE_API_TOKEN else {}
    response = requests.get(url, headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    data = [payload] if core_user_id else payload.get('results', [])
    report = {'created': 0, 'updated': 0, 'errors': []}
    now = timezone.now()
    for item in data:
        try:
            core_id = item.get('id')
            code = item.get('code') or item.get('username')
            username = item.get('username') or code
            obj, created = SafetyUser.objects.get_or_create(
                core_user_id=core_id,
                defaults={'code': code, 'username': username}
            )
            obj.code = code
            obj.username = username
            obj.first_name = item.get('first_name') or ''
            obj.last_name = item.get('last_name') or ''
            obj.email = item.get('email') or ''
            obj.formation_code = item.get('formation_code') or ''
            obj.formation_name = item.get('formation_name') or ''
            obj.class_name = item.get('class_name') or ''
            obj.group_name = item.get('group_name') or ''
            obj.role_principal = item.get('role_principal') or 'utilisateur'
            obj.rights = item.get('rights') or ''
            obj.active = bool(item.get('active', True))
            obj.school_year = item.get('school_year') or ''
            obj.synced_at = now
            initial_password = item.get('initial_password') or ''
            if initial_password and (created or force_password or settings.SAFETY_RESET_PASSWORDS_ON_SYNC):
                obj.set_password(initial_password)
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('username') or item.get('code')}: {exc}")
    return report
