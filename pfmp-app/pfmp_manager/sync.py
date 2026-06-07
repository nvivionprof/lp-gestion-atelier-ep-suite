from django.conf import settings
from django.utils import timezone
import requests
from .models import PfmpUser, Formation

def _headers():
    return {'X-API-Key': settings.LP_CORE_API_TOKEN} if settings.LP_CORE_API_TOKEN else {}

def sync_users_from_lp_core(timeout=90, force_password=False, core_user_id=None):
    api_url=settings.LP_CORE_API_URL.rstrip('/')
    url=f'{api_url}/api/users/{core_user_id}/' if core_user_id else f'{api_url}/api/users/'
    r=requests.get(url, headers=_headers(), timeout=timeout); r.raise_for_status()
    payload=r.json(); data=[payload] if core_user_id else payload.get('results', [])
    report={'created':0,'updated':0,'formations_created':0,'formations_updated':0,'errors':[]}
    now=timezone.now()
    for item in data:
        try:
            f_code=item.get('formation_code') or ''
            f_name=item.get('formation_name') or f_code
            if f_code:
                f=Formation.objects.filter(code=f_code).first()
                created=False
                if f is None:
                    f=Formation(code=f_code, nom=f_name or f_code); created=True
                f.nom=f_name or f.code; f.active=True; f.save()
                report['formations_created' if created else 'formations_updated']+=1
            core_id=item.get('id'); code=item.get('code') or item.get('username'); username=item.get('username') or code
            obj=None
            if core_id is not None: obj=PfmpUser.objects.filter(core_user_id=core_id).first()
            if obj is None: obj=PfmpUser.objects.filter(username=username).first()
            created=False
            if obj is None:
                obj=PfmpUser(core_user_id=core_id, code=code, username=username); created=True
            elif core_id is not None and not obj.core_user_id:
                obj.core_user_id=core_id
            obj.code=code or obj.code; obj.username=username or obj.username
            obj.first_name=item.get('first_name') or ''; obj.last_name=item.get('last_name') or ''; obj.email=item.get('email') or ''
            obj.formation_code=f_code; obj.formation_name=f_name or ''; obj.class_name=item.get('class_name') or ''; obj.group_name=item.get('group_name') or ''
            obj.role_principal=item.get('role_principal') or 'utilisateur'; obj.rights=item.get('rights') or ''; obj.active=bool(item.get('active', True)); obj.school_year=item.get('school_year') or ''; obj.synced_at=now
            initial=item.get('initial_password') or ''
            if initial and (created or force_password or settings.PFMP_RESET_PASSWORDS_ON_SYNC): obj.set_password(initial)
            obj.save(); report['created' if created else 'updated']+=1
        except Exception as exc:
            report['errors'].append(f"{item.get('username') or item.get('code')}: {exc}")
    return report

def sync_formations_from_lp_core(timeout=90):
    r=requests.get(settings.LP_CORE_API_URL.rstrip()+'/api/formations/', headers=_headers(), timeout=timeout); r.raise_for_status()
    report={'created':0,'updated':0,'errors':[]}
    for item in r.json().get('results',[]):
        try:
            code=item.get('code') or f"CORE_{item.get('id') or 'FORMATION'}"; nom=item.get('name') or code
            obj=Formation.objects.filter(code=code).first(); created=False
            if obj is None: obj=Formation(code=code, nom=nom); created=True
            obj.core_formation_id=item.get('id'); obj.nom=nom; obj.active=bool(item.get('active', True)); obj.save()
            report['created' if created else 'updated']+=1
        except Exception as exc: report['errors'].append(f"{item.get('code')}: {exc}")
    return report
