from django.conf import settings
from .permissions import current_safety_user

def safety_context(request):
    return {
        'SAFETY_APP_NAME': getattr(settings, 'SAFETY_APP_NAME', 'Safety Manager'),
        'SAFETY_VERSION': getattr(settings, 'SAFETY_VERSION', 'Safety Manager — Bêta V0.0.1'),
        'SAFETY_PUBLIC_URL': getattr(settings, 'SAFETY_PUBLIC_URL', ''),
        'LP_CORE_PUBLIC_URL': getattr(settings, 'LP_CORE_PUBLIC_URL', ''),
        'TOOLMAG_PUBLIC_BASE_URL': getattr(settings, 'TOOLMAG_PUBLIC_BASE_URL', ''),
        'safety_current_user': current_safety_user(request),
    }
