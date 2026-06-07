"""Synchronisation LP Core → PedaShop.

La fonction télécharge les utilisateurs via l’API LP Core. PedaShop ne dépend
pas de la structure SQL de LP Core, ce qui permet de faire évoluer chaque module
sans casser les autres.
"""
from django.conf import settings
from django.utils import timezone
import requests
from .models import PedaShopUser, Magasin


def sync_users_from_lp_core(reset_passwords: bool | None = None, *, timeout: int = 90, core_user_id=None) -> dict:
    if reset_passwords is None:
        reset_passwords = settings.PEDASHOP_RESET_PASSWORDS_ON_SYNC
    url = f"{settings.LP_CORE_API_URL}/api/users/"
    headers = {'X-API-Key': settings.LP_CORE_API_TOKEN} if settings.LP_CORE_API_TOKEN else {}
    endpoint = f"{url.rstrip('/')}/{core_user_id}/" if core_user_id else url
    response = requests.get(endpoint, headers=headers, timeout=timeout)
    response.raise_for_status()
    payload = response.json()
    rows = [payload] if core_user_id else payload.get('results', [])
    report = {'created': 0, 'updated': 0, 'disabled': 0}
    seen_ids = []
    for item in rows:
        core_id = item.get('id')
        if core_id:
            seen_ids.append(core_id)
        user, created = PedaShopUser.objects.get_or_create(
            core_user_id=core_id,
            defaults={'code': item.get('code') or item.get('username'), 'username': item.get('username') or item.get('code')}
        )
        user.code = item.get('code') or user.code
        user.username = item.get('username') or user.username
        user.first_name = item.get('first_name') or ''
        user.last_name = item.get('last_name') or ''
        user.email = item.get('email') or ''
        user.formation_code = item.get('formation_code') or ''
        user.formation_name = item.get('formation_name') or ''
        user.class_name = item.get('class_name') or ''
        user.group_name = item.get('group_name') or ''
        user.role_principal = item.get('role_principal') or 'utilisateur'
        user.rights = item.get('rights') or ''
        user.school_year = item.get('school_year') or ''
        user.active = bool(item.get('active', True))
        user.synced_at = timezone.now()
        initial_password = item.get('initial_password')
        if initial_password and (created or reset_passwords or not user.password_hash):
            user.set_password(initial_password)
        user.save()

        # Magasins visibles pilotés depuis LP Core. Si LP Core transmet un
        # magasin encore absent dans PedaShop, il est créé comme magasin actif
        # minimal afin que la synchronisation ne bloque jamais.
        magasins_payload = item.get('pedashop_magasins') or []
        if magasins_payload:
            magasins = []
            for mag in magasins_payload:
                code = (mag.get('code') or '').strip().upper()
                if not code:
                    continue
                magasin, _ = Magasin.objects.get_or_create(code=code, defaults={'nom': mag.get('nom') or code})
                if mag.get('nom') and magasin.nom != mag.get('nom'):
                    magasin.nom = mag.get('nom')
                    magasin.save(update_fields=['nom'])
                magasins.append(magasin)
            user.magasins_visibles.set(magasins)

        report['created' if created else 'updated'] += 1
    if seen_ids and not core_user_id:
        report['disabled'] = PedaShopUser.objects.exclude(core_user_id__in=seen_ids).update(active=False)
    return report
