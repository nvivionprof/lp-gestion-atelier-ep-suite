from django.conf import settings
from .permissions import current_user


def pedashop_context(request):
    return {
        'PEDASHOP_APP_NAME': settings.PEDASHOP_APP_NAME,
        'PEDASHOP_VERSION': settings.PEDASHOP_VERSION,
        'LP_CORE_PUBLIC_URL': settings.LP_CORE_PUBLIC_URL,
        'TOOLMAG_PUBLIC_BASE_URL': settings.TOOLMAG_PUBLIC_BASE_URL,
        'SAFETY_PUBLIC_URL': settings.SAFETY_PUBLIC_URL,
        'PEDASHOP_PUBLIC_URL': settings.PEDASHOP_PUBLIC_URL,
        'pedashop_current_user': current_user(request),
    }
