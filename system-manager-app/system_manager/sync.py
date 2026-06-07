from __future__ import annotations
from django.conf import settings
from django.utils import timezone
import requests
from .models import SystemUser, Formation, Niveau, SchoolClass, WorkshopZone, WorkshopSubZone, normalize_code


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
                formation_code_norm = normalize_code(formation_code, 'FORMATION', 40)
                formation = Formation.objects.filter(code=formation_code_norm).order_by('id').first()
                f_created = False
                if formation is None:
                    formation = Formation(code=formation_code_norm, nom=formation_name or formation_code_norm)
                    f_created = True
                formation.nom = formation_name or formation.code
                formation.active = True
                formation.save()
                report['formations_created' if f_created else 'formations_updated'] += 1
            core_id = item.get('id')
            code = item.get('code') or item.get('username')
            username = item.get('username') or code
            obj, created = SystemUser.objects.get_or_create(core_user_id=core_id, defaults={'code': code, 'username': username})
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
            if initial_password and (created or force_password or settings.SYSTEM_MANAGER_RESET_PASSWORDS_ON_SYNC):
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
            raw_code = item.get('code') or item.get('name') or f'CORE_{core_id or "FORMATION"}'
            code = normalize_code(raw_code, 'FORMATION', 40)
            nom = item.get('name') or item.get('code') or code
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


def sync_workshop_blocks_from_lp_core(timeout=90):
    """Synchronise les blocs atelier LP Core vers System Manager."""
    from .models import WorkshopBlock, WorkshopBlockSlot, Niveau, SchoolClass
    url = settings.LP_CORE_API_URL.rstrip('/') + '/api/atelier-blocks/'
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    data = response.json().get('results', [])
    report = {'created': 0, 'updated': 0, 'slots_created': 0, 'slots_updated': 0, 'errors': []}
    for item in data:
        try:
            core_id = item.get('id')
            code = normalize_code(item.get('code') or item.get('name') or f'BLOC_{core_id}', 'BLOC', 80)
            obj = WorkshopBlock.objects.filter(core_block_id=core_id).first() if core_id is not None else None
            if obj is None:
                obj = WorkshopBlock.objects.filter(code=code).first()
            created = False
            if obj is None:
                obj = WorkshopBlock(core_block_id=core_id, code=code)
                created = True
            obj.core_block_id = core_id
            obj.code = code
            obj.nom = item.get('name') or code
            obj.description = item.get('description') or ''
            obj.active = bool(item.get('active', True))
            obj.save()
            obj.classes.clear()
            class_ids = item.get('class_ids', []) or []
            if class_ids:
                for cid in class_ids:
                    c = SchoolClass.objects.filter(core_class_id=cid).order_by('-active', 'id').first()
                    if c:
                        obj.classes.add(c)
            else:
                for cname in item.get('class_names', []):
                    c = SchoolClass.objects.filter(nom=cname).order_by('-active', 'id').first()
                    if c:
                        obj.classes.add(c)
            obj.formations.clear()
            for fcode in item.get('formation_codes', []):
                f = Formation.objects.filter(code=normalize_code(fcode, 'FORMATION', 40)).first()
                if f:
                    obj.formations.add(f)
            obj.niveaux.clear()
            for ncode in item.get('niveau_codes', []):
                n = Niveau.objects.filter(code=normalize_code(ncode, 'NIVEAU', 40)).first()
                if n:
                    obj.niveaux.add(n)
            report['created' if created else 'updated'] += 1
            for slot in item.get('slots', []):
                day = int(slot.get('day_of_week'))
                start = slot.get('start_time')
                end = slot.get('end_time')
                sobj, screated = WorkshopBlockSlot.objects.get_or_create(block=obj, day_of_week=day, start_time=start, end_time=end, defaults={'label': slot.get('label') or '', 'active': bool(slot.get('active', True))})
                sobj.label = slot.get('label') or sobj.label
                sobj.active = bool(slot.get('active', True))
                sobj.save()
                report['slots_created' if screated else 'slots_updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('code')}: {exc}")
    return report



def sync_classes_from_lp_core(timeout=90):
    """Synchronise les classes LP Core vers System Manager."""
    url = settings.LP_CORE_API_URL.rstrip('/') + '/api/classes/'
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    data = response.json().get('results', [])
    report = {'created': 0, 'updated': 0, 'errors': []}
    for item in data:
        try:
            core_id = item.get('id')
            name = item.get('name') or ''
            fcode = normalize_code(item.get('formation_code') or '', 'FORMATION', 40) if item.get('formation_code') else ''
            formation = Formation.objects.filter(code=fcode).first() if fcode else None
            obj = SchoolClass.objects.filter(core_class_id=core_id).first() if core_id else None
            if obj is None:
                obj = SchoolClass.objects.filter(nom=name, school_year=item.get('school_year') or '').first()
            created = False
            if obj is None:
                obj = SchoolClass(core_class_id=core_id, nom=name)
                created = True
            obj.core_class_id = core_id
            obj.nom = name
            obj.formation = formation
            obj.formation_code = fcode
            obj.school_year = item.get('school_year') or ''
            obj.active = bool(item.get('active', True))
            obj.save()
            report['created' if created else 'updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('name')}: {exc}")
    return report


def sync_workshop_zones_from_lp_core(timeout=90):
    """Synchronise les zones/sous-zones LP Core vers System Manager."""
    url = settings.LP_CORE_API_URL.rstrip('/') + '/api/workshop-zones/'
    response = requests.get(url, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    data = response.json().get('results', [])
    report = {'zones_created': 0, 'zones_updated': 0, 'subzones_created': 0, 'subzones_updated': 0, 'errors': []}
    for item in data:
        try:
            code = normalize_code(item.get('code') or item.get('name') or 'ZONE', 'ZONE', 40)
            zone, created = WorkshopZone.objects.get_or_create(code=code, defaults={'nom': item.get('name') or code})
            zone.nom = item.get('name') or zone.nom
            zone.description = item.get('description') or ''
            zone.active = bool(item.get('active', True))
            zone.ordre_affichage = int(item.get('order') or zone.ordre_affichage or 100)
            zone.save()
            report['zones_created' if created else 'zones_updated'] += 1
            for child in item.get('subzones', []):
                scode = normalize_code(child.get('code') or child.get('name') or 'SOUS_ZONE', 'SOUS_ZONE', 40)
                sub, sub_created = WorkshopSubZone.objects.get_or_create(zone=zone, code=scode, defaults={'nom': child.get('name') or scode})
                sub.nom = child.get('name') or sub.nom
                sub.description = child.get('description') or ''
                sub.active = bool(child.get('active', True))
                sub.ordre_affichage = int(child.get('order') or sub.ordre_affichage or 100)
                sub.save()
                report['subzones_created' if sub_created else 'subzones_updated'] += 1
        except Exception as exc:
            report['errors'].append(f"{item.get('code')}: {exc}")
    return report


def push_workshop_referentials_to_lp_core(timeout=90):
    """Pousse les zones, sous-zones et blocs System Manager vers LP Core si l'API LP Core l'autorise.

    Les anciennes versions de LP Core peuvent ne pas exposer les endpoints d'import ; dans ce cas
    l'appel remonte une erreur claire sans modifier les données locales.
    """
    from .models import WorkshopBlock, WorkshopBlockSlot
    api_url = settings.LP_CORE_API_URL.rstrip('/')
    zones_payload = []
    for zone in WorkshopZone.objects.prefetch_related('sous_zones').filter(active=True).order_by('ordre_affichage', 'code'):
        zones_payload.append({
            'code': zone.code,
            'name': zone.nom,
            'description': zone.description,
            'order': zone.ordre_affichage,
            'active': zone.active,
            'subzones': [
                {'code': sub.code, 'name': sub.nom, 'description': sub.description, 'order': sub.ordre_affichage, 'active': sub.active}
                for sub in zone.sous_zones.filter(active=True).order_by('ordre_affichage', 'code')
            ],
        })
    blocks_payload = []
    for block in WorkshopBlock.objects.prefetch_related('classes', 'slots').filter(active=True).order_by('code'):
        blocks_payload.append({
            'code': block.code,
            'name': block.nom,
            'description': block.description,
            'active': block.active,
            'class_names': list(block.classes.filter(active=True).values_list('nom', flat=True)),
            'slots': [
                {'day_of_week': slot.day_of_week, 'label': slot.label, 'start_time': slot.start_time.strftime('%H:%M'), 'end_time': slot.end_time.strftime('%H:%M'), 'active': slot.active}
                for slot in block.slots.filter(active=True).order_by('day_of_week', 'start_time')
            ],
        })
    payload = {'zones': zones_payload, 'blocks': blocks_payload}
    url = f'{api_url}/api/system-manager/referentials/import/'
    response = requests.post(url, json=payload, headers=_headers(), timeout=timeout)
    response.raise_for_status()
    try:
        return response.json()
    except Exception:
        return {'status': response.status_code, 'detail': response.text[:500]}
