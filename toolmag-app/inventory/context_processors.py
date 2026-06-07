from django.utils import translation
from django.conf import settings
from .models import Person


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
    return {
        'tm_current_storekeeper': storekeeper,
        'tm_current_borrower': borrower,
        'tm_is_prof': is_prof,
        'TOOLMAG_VERSION_LABEL': version,
        'TOOLMAG_VERSION_DETAIL': version,
        'TOOLMAG_LANG': (request.session.get('toolmag_lang') or translation.get_language() or 'fr')[:2],
        'LP_CORE_PUBLIC_URL': getattr(settings, 'LP_CORE_PUBLIC_URL', ''),
    }
