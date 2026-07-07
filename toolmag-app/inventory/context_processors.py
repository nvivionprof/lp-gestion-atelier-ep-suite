from django.utils import translation
from django.conf import settings
from .models import Person


def _person_label(person):
    if not person:
        return ''
    first = (getattr(person, 'first_name', '') or '').strip()
    last = (getattr(person, 'last_name', '') or '').strip()
    full = f"{first} {last}".strip()
    return full or getattr(person, 'name', '') or getattr(person, 'username', '') or getattr(person, 'code', '')


def _person_from_session(code, *, require_storekeeper=False):
    if not code:
        return None
    person = Person.objects.filter(code=code, active=True, archived=False).first()
    if not person:
        return None
    if require_storekeeper and not person.has_role(Person.Role.STOREKEEPER, Person.Role.RESPONSIBLE, Person.Role.ADMIN):
        return None
    return person


def toolmag_context(request):
    storekeeper = _person_from_session(request.session.get('storekeeper_code'), require_storekeeper=True)
    borrower = _person_from_session(request.session.get('borrower_code'))
    is_prof = bool(storekeeper and storekeeper.role in [Person.Role.RESPONSIBLE, Person.Role.ADMIN])
    version = getattr(settings, 'APP_VERSION', 'ToolMag — Bêta V0.0.1')
    lp_core_url = getattr(settings, 'LP_CORE_PUBLIC_URL', '').rstrip('/')
    return {
        'tm_current_storekeeper': storekeeper,
        'tm_current_borrower': borrower,
        'tm_current_storekeeper_label': _person_label(storekeeper),
        'tm_current_borrower_label': _person_label(borrower),
        'tm_is_prof': is_prof,
        'TOOLMAG_VERSION_LABEL': version,
        'TOOLMAG_VERSION_DETAIL': version,
        'TOOLMAG_LANG': (request.session.get('toolmag_lang') or translation.get_language() or 'fr')[:2],
        'LP_CORE_PUBLIC_URL': lp_core_url,
        'SUITE_APP_LINKS': [
            {'name': 'LP Core', 'url': '/'},
            {'name': 'Safety Manager', 'url': '/safety/'},
            {'name': 'PedaShop', 'url': '/pedashop/'},
            {'name': 'System Manager', 'url': '/system/'},
            {'name': 'TP Manager', 'url': '/tpmanager/'},
            {'name': 'PFMP Manager', 'url': '/pfmp/'},
            {'name': 'LP Display Manager', 'url': '/lpdisplaymanager/'},
        ],
    }
