import requests
from django.conf import settings
from .models import Formation, SchoolClass, Person

ROLE_MAP = {
    'utilisateur': Person.Role.USER,
    'eleve': Person.Role.USER,
    'magasinier': Person.Role.STOREKEEPER,
    'professeur': Person.Role.RESPONSIBLE,
    'responsable': Person.Role.RESPONSIBLE,
    'admin': Person.Role.ADMIN,
    'lecture_seule': Person.Role.READ_ONLY,
}

RIGHT_ROLE_MAP = {
    'MAGASINIER': Person.Role.STOREKEEPER,
    'TOOLMAG_ADMIN': Person.Role.RESPONSIBLE,
    'ADMIN': Person.Role.ADMIN,
    'ALL': Person.Role.ADMIN,
}


def role_from_core(payload):
    rights = {r.strip().upper() for r in (payload.get('rights') or '').replace(',', ';').split(';') if r.strip()}
    for right, role in RIGHT_ROLE_MAP.items():
        if right in rights:
            return role
    return ROLE_MAP.get((payload.get('role_principal') or '').lower(), Person.Role.USER)


def sync_users_from_lp_core(*, timeout=90, force_password=False, core_user_id=None):
    api_url = getattr(settings, 'LP_CORE_API_URL', 'http://lp-core-app:8000').rstrip('/')
    token = getattr(settings, 'LP_CORE_API_TOKEN', '') or ''
    headers = {'X-API-Key': token} if token else {}
    endpoint = f'{api_url}/api/users/{core_user_id}/' if core_user_id else f'{api_url}/api/users/'
    response = requests.get(endpoint, headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    rows = [payload] if core_user_id else payload.get('results', [])
    created = updated = skipped = 0
    errors = []
    for row in rows:
        try:
            formation_code = row.get('formation_code') or 'GEN'
            formation_name = row.get('formation_name') or formation_code
            formation, _ = Formation.objects.get_or_create(code=formation_code, defaults={'name': formation_name})
            if not formation.name or formation.name == formation.code:
                formation.name = formation_name
                formation.save(update_fields=['name', 'updated_at'])
            class_name = row.get('class_name') or ''
            if class_name:
                SchoolClass.objects.get_or_create(formation=formation, name=class_name)
            code = row.get('code') or row.get('username')
            if not code:
                skipped += 1
                continue
            role = role_from_core(row)
            allowed_roles = row.get('rights') or ''
            defaults = {
                'username': row.get('username') or code,
                'first_name': row.get('first_name') or '',
                'last_name': row.get('last_name') or '',
                'email': row.get('email') or '',
                'role': role,
                'allowed_roles': allowed_roles,
                'formation': formation,
                'class_name': class_name,
                'group_name': row.get('group_name') or '',
                'active': bool(row.get('active', True)),
                'archived': False,
            }
            person, was_created = Person.objects.update_or_create(code=code, defaults=defaults)
            initial_password = row.get('initial_password') or ''
            if initial_password and (was_created or force_password or not person.password_hash):
                person.set_password(initial_password)
                person.must_change_password = True
                person.save(update_fields=['password_hash', 'must_change_password', 'updated_at'])
            if was_created:
                created += 1
            else:
                updated += 1
        except Exception as exc:
            errors.append(f"{row.get('code') or row.get('username')}: {exc}")
    return {'created': created, 'updated': updated, 'skipped': skipped, 'errors': errors, 'source': api_url}
