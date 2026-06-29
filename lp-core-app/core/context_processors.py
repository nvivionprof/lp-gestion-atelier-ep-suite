from django.conf import settings
from django.core import signing
from urllib.parse import quote
from .models import CoreUser, CoreModuleAccessRule, PublicSuiteSettings

SUITE_VERSION_LABEL = 'RC V0.0.1'

MODULE_DEFINITIONS = [
    {'code': 'toolmag', 'name': 'ToolMag', 'subtitle': 'Magasin outillage', 'version': SUITE_VERSION_LABEL, 'url_attr': 'TOOLMAG_PUBLIC_BASE_URL', 'icon': 'core/img/logo-toolmag-launcher.png', 'default_roles': {'eleve', 'utilisateur', 'magasinier', 'professeur', 'responsable', 'admin'}},
    {'code': 'safety', 'name': 'Safety Manager', 'subtitle': 'Sécurité atelier & DUERP', 'version': SUITE_VERSION_LABEL, 'url_attr': 'SAFETY_PUBLIC_URL', 'icon': 'core/img/logo-safety-launcher.png', 'default_roles': {'eleve', 'utilisateur', 'magasinier', 'professeur', 'responsable', 'admin'}},
    {'code': 'pedashop', 'name': 'PedaShop', 'subtitle': 'Magasin consommables multi-site', 'version': SUITE_VERSION_LABEL, 'url_attr': 'PEDASHOP_PUBLIC_URL', 'fallback_attr': 'CONSUMABLES_PUBLIC_URL', 'icon': 'core/img/logo-pedashop-launcher.png', 'default_roles': {'eleve', 'utilisateur', 'magasinier', 'professeur', 'responsable', 'admin'}},
    {'code': 'system', 'name': 'System Manager', 'subtitle': 'Systèmes pédagogiques, réservations & QR codes', 'version': SUITE_VERSION_LABEL, 'url_attr': 'SYSTEM_MANAGER_PUBLIC_URL', 'fallback_attr': 'INVENTORY_PUBLIC_URL', 'icon': 'core/img/logo-system-manager-launcher.png', 'default_roles': {'eleve', 'utilisateur', 'magasinier', 'professeur', 'responsable', 'admin'}},
    {'code': 'tpmanager', 'name': 'TP Manager', 'subtitle': 'Base documentaire TP, parcours élèves & compétences', 'version': SUITE_VERSION_LABEL, 'url_attr': 'TPMANAGER_PUBLIC_URL', 'icon': 'core/img/logo-tpmanager-launcher.png', 'default_roles': {'professeur', 'responsable', 'admin'}},
    {'code': 'pfmp', 'name': 'PFMP Manager', 'subtitle': 'Entreprises, périodes PFMP, démarches et portail entreprise', 'version': SUITE_VERSION_LABEL, 'url_attr': 'PFMP_PUBLIC_URL', 'icon': 'core/img/logo-pfmp-manager-launcher.png', 'default_roles': {'eleve', 'utilisateur', 'professeur', 'responsable', 'admin'}},
    {'code': 'lpdisplaymanager', 'name': 'LP Display Manager', 'subtitle': 'Affichage dynamique, écrans, campagnes et players Raspberry', 'version': SUITE_VERSION_LABEL, 'url_attr': 'LPDISPLAY_PUBLIC_URL', 'icon': 'core/img/logo-lp-suite.png', 'default_roles': {'professeur', 'responsable', 'admin'}},
]


def _current_user(request):
    uid = request.session.get('core_user_id')
    if not uid:
        return None
    user = CoreUser.objects.filter(id=uid, active=True).first()
    if user is None:
        request.session.pop('core_user_id', None)
        request.session.modified = True
    return user


EXPECTED_MODULE_PATHS = {
    'toolmag': '/toolmag/',
    'safety': '/safety/',
    'pedashop': '/pedashop/',
    'system': '/system/',
    'tpmanager': '/tpmanager/',
    'pfmp': '/pfmp/',
    'lpdisplaymanager': '/lpdisplaymanager/',
}


def _request_base_url(request):
    """Build the public base URL from the current request.

    This avoids stale private-IP launcher links after switching to a DuckDNS
    domain. When the suite is used behind the single gateway, all applications
    live under the same origin and only the path changes.
    """
    try:
        scheme = request.headers.get('X-Forwarded-Proto') or request.scheme or 'http'
        host = request.headers.get('X-Forwarded-Host') or request.get_host()
        if host:
            return f'{scheme}://{host}'.rstrip('/')
    except Exception:
        pass
    return ''


def _settings_module_urls():
    try:
        obj = PublicSuiteSettings.get_solo()
        return obj.module_urls()
    except Exception:
        return {}


def _base_public_url(request=None):
    configured = (getattr(settings, 'LP_CORE_PUBLIC_URL', '') or '').rstrip('/')
    if request is not None:
        current = _request_base_url(request)
        # Prefer the real host used by the browser when the configured URL is
        # still localhost or a private RFC1918 address.
        if current and (not configured or 'localhost' in configured or '127.0.0.1' in configured or '192.168.' in configured or '10.' in configured or '172.16.' in configured):
            return current
    return configured


def _url_for(defn, request=None):
    """Return a deterministic public module URL.

    Priority order:
    1. current browser origin + gateway path, to avoid stale IP links;
    2. PublicSuiteSettings stored in LP Core;
    3. Django environment settings.
    """
    expected_path = EXPECTED_MODULE_PATHS.get(defn.get('code'))
    base = _base_public_url(request)
    if base and expected_path:
        return f"{base}{expected_path.rstrip('/')}"
    db_urls = _settings_module_urls()
    value = db_urls.get(defn.get('url_attr')) or getattr(settings, defn['url_attr'], '')
    if not value and defn.get('fallback_attr'):
        value = db_urls.get(defn.get('fallback_attr')) or getattr(settings, defn['fallback_attr'], '')
    return (value or '#').rstrip('/')


def lp_suite_sso_url_for(user, defn, request=None):
    """Return a module URL carrying a short-lived LP Core SSO token.

    Modules remain usable directly with their own login pages. When opened from
    LP Core by an authenticated user, the module can establish its local session
    without asking for the password again.
    """
    base = _url_for(defn, request)
    if not user or base == '#':
        return base
    token = signing.dumps({
        'code': user.code,
        'username': user.username,
        'role': user.role_principal,
    }, key=getattr(settings, 'LP_CORE_API_TOKEN', ''), salt='lp-suite-sso')
    return f"{base}/portal-login/?token={quote(token)}"


def _can_see_module(user, module_code, default_roles):
    if not user:
        return False
    if user.is_admin_like:
        return True
    active_rules = list(CoreModuleAccessRule.objects.filter(module=module_code, active=True))
    if active_rules:
        return any(rule.matches(user) for rule in active_rules)
    return user.role_principal in default_roles


def core_context(request):
    user = _current_user(request)
    modules = []
    for item in MODULE_DEFINITIONS:
        enabled = _can_see_module(user, item['code'], item['default_roles']) if user else False
        modules.append({
            'code': item['code'],
            'name': item['name'],
            'subtitle': item['subtitle'],
            'version': item['version'],
            'url': lp_suite_sso_url_for(user, item, request),
            'icon': item['icon'],
            'status': 'Disponible' if enabled else 'Masqué par droits',
            'enabled': enabled,
        })
    visible_modules = [m for m in modules if m['enabled']]
    return {
        'CORE_APP_NAME': settings.LP_CORE_PUBLIC_NAME,
        'CORE_VERSION': settings.LP_CORE_VERSION,
        'SUITE_VERSION_LABEL': SUITE_VERSION_LABEL,
        'LP_CORE_PUBLIC_URL': _base_public_url(request),
        'TOOLMAG_PUBLIC_BASE_URL': _url_for({'code': 'toolmag', 'url_attr': 'TOOLMAG_PUBLIC_BASE_URL'}, request),
        'SAFETY_PUBLIC_URL': _url_for({'code': 'safety', 'url_attr': 'SAFETY_PUBLIC_URL'}, request),
        'PEDASHOP_PUBLIC_URL': _url_for({'code': 'pedashop', 'url_attr': 'PEDASHOP_PUBLIC_URL'}, request),
        'SYSTEM_MANAGER_PUBLIC_URL': _url_for({'code': 'system', 'url_attr': 'SYSTEM_MANAGER_PUBLIC_URL'}, request),
        'TPMANAGER_PUBLIC_URL': _url_for({'code': 'tpmanager', 'url_attr': 'TPMANAGER_PUBLIC_URL'}, request),
        'LPDISPLAY_PUBLIC_URL': _url_for({'code': 'lpdisplaymanager', 'url_attr': 'LPDISPLAY_PUBLIC_URL'}, request),
        'suite_modules': visible_modules,
        'suite_modules_all': modules,
        'core_current_user': user,
    }
