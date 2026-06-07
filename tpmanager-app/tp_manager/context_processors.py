from django.conf import settings
from .models import TpUser


def current_tp_user(request):
    uid = request.session.get('tp_user_id')
    if not uid:
        return None
    return TpUser.objects.filter(id=uid, active=True).first()


def tp_context(request):
    return {
        'TPMANAGER_APP_NAME': settings.TPMANAGER_APP_NAME,
        'TPMANAGER_VERSION': settings.TPMANAGER_VERSION,
        'LP_CORE_PUBLIC_URL': settings.LP_CORE_PUBLIC_URL,
        'TOOLMAG_PUBLIC_BASE_URL': settings.TOOLMAG_PUBLIC_BASE_URL,
        'SAFETY_PUBLIC_URL': settings.SAFETY_PUBLIC_URL,
        'PEDASHOP_PUBLIC_URL': settings.PEDASHOP_PUBLIC_URL,
        'SYSTEM_MANAGER_PUBLIC_URL': settings.SYSTEM_MANAGER_PUBLIC_URL,
        'TPMANAGER_PUBLIC_URL': settings.TPMANAGER_PUBLIC_URL,
        'tp_current_user': current_tp_user(request),
    }
