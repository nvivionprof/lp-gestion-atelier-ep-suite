from django.conf import settings
from .permissions import current_system_user, can_create_systems, can_edit_systems


def _rights(user):
    if not user:
        return set()
    try:
        return {str(x).upper() for x in user.rights_list()}
    except Exception:
        return set()


def _role(user):
    return (getattr(user, 'role_principal', '') or '').lower()


def _can_see_suite_app(user, code):
    # Filtrage d'affichage du menu Suite côté System Manager.
    # La sécurité réelle reste portée par chaque module et par LP Core.
    if code in {'core', 'system'}:
        return True
    if not user:
        return False
    if getattr(user, 'is_admin_like', False) or getattr(user, 'is_prof_like', False):
        return True
    rights = _rights(user)
    role = _role(user)
    if code == 'toolmag':
        return bool({'TOOLMAG', 'MATERIEL', 'MATERIAL', 'MAGASIN', 'MAGASINIER', 'OUTILLAGE'} & rights) or role in {'magasinier', 'utilisateur', 'eleve'}
    if code == 'safety':
        return bool({'SAFETY', 'SECURITE', 'DUERP', 'RISK', 'HABILITATION'} & rights)
    if code == 'pedashop':
        return bool({'PEDASHOP', 'CONSOMMABLES', 'STOCK', 'MAGASIN', 'MAGASINIER'} & rights) or role == 'magasinier'
    if code == 'tpmanager':
        return bool({'TPMANAGER', 'TP', 'SEQUENCE', 'EVALUATION'} & rights)
    if code == 'pfmp':
        return bool({'PFMP', 'STAGE', 'ENTREPRISE'} & rights) or role in {'eleve', 'utilisateur'}
    return False


SUITE_PATHS = {
    'core': '/',
    'toolmag': '/toolmag/',
    'safety': '/safety/',
    'pedashop': '/pedashop/',
    'system': '/system/',
    'tpmanager': '/tpmanager/',
    'pfmp': '/pfmp/',
}


def _request_base_url(request):
    try:
        scheme = request.headers.get('X-Forwarded-Proto') or request.scheme or 'http'
        host = request.headers.get('X-Forwarded-Host') or request.get_host()
        if host:
            return f'{scheme}://{host}'.rstrip('/')
    except Exception:
        pass
    return ''


def _public_url(request, code, configured):
    base = _request_base_url(request)
    path = SUITE_PATHS.get(code, '/')
    # Prefer current origin when configured URLs still contain a private IP or localhost.
    stale = any(x in (configured or '') for x in ('localhost', '127.0.0.1', '192.168.', '10.', '172.16.'))
    if base and (stale or not configured):
        return f'{base}{path}'.rstrip('/')
    return (configured or '').rstrip('/')


def _suite_links(user, request):
    defs = [
        ('core', 'LP Core', getattr(settings, 'LP_CORE_PUBLIC_URL', '')),
        ('toolmag', 'ToolMag', getattr(settings, 'TOOLMAG_PUBLIC_BASE_URL', '')),
        ('safety', 'Safety Manager', getattr(settings, 'SAFETY_PUBLIC_URL', '')),
        ('pedashop', 'PedaShop', getattr(settings, 'PEDASHOP_PUBLIC_URL', '')),
        ('system', 'System Manager', getattr(settings, 'SYSTEM_MANAGER_PUBLIC_URL', '')),
        ('tpmanager', 'TP Manager', getattr(settings, 'TPMANAGER_PUBLIC_URL', '')),
        ('pfmp', 'PFMP Manager', getattr(settings, 'PFMP_PUBLIC_URL', '')),
    ]
    return [{'code': code, 'name': name, 'url': _public_url(request, code, url)} for code, name, url in defs if _can_see_suite_app(user, code)]


def system_context(request):
    user = current_system_user(request)
    return {
        'SYSTEM_MANAGER_APP_NAME': getattr(settings, 'SYSTEM_MANAGER_APP_NAME', 'System Manager'),
        'SYSTEM_MANAGER_VERSION': getattr(settings, 'SYSTEM_MANAGER_VERSION', 'System Manager — Bêta V0.0.1'),
        'SYSTEM_MANAGER_PUBLIC_URL': _public_url(request, 'system', getattr(settings, 'SYSTEM_MANAGER_PUBLIC_URL', '')),
        'LP_CORE_PUBLIC_URL': _public_url(request, 'core', getattr(settings, 'LP_CORE_PUBLIC_URL', '')),
        'TOOLMAG_PUBLIC_BASE_URL': _public_url(request, 'toolmag', getattr(settings, 'TOOLMAG_PUBLIC_BASE_URL', '')),
        'SAFETY_PUBLIC_URL': _public_url(request, 'safety', getattr(settings, 'SAFETY_PUBLIC_URL', '')),
        'PEDASHOP_PUBLIC_URL': _public_url(request, 'pedashop', getattr(settings, 'PEDASHOP_PUBLIC_URL', '')),
        'TPMANAGER_PUBLIC_URL': _public_url(request, 'tpmanager', getattr(settings, 'TPMANAGER_PUBLIC_URL', '')),
        'PFMP_PUBLIC_URL': _public_url(request, 'pfmp', getattr(settings, 'PFMP_PUBLIC_URL', '')),
        'suite_app_links': _suite_links(user, request),
        'system_current_user': user,
        'system_can_create': can_create_systems(user),
        'system_can_edit': can_edit_systems(user),
        'system_is_admin': bool(user and user.is_admin_like),
    }
