from django.conf import settings
from .models import PfmpUser

def current_pfmp_user(request):
    uid = request.session.get('pfmp_user_id')
    if not uid:
        return None
    user = PfmpUser.objects.filter(id=uid, active=True).first()
    if user is None:
        request.session.pop('pfmp_user_id', None)
        request.session.pop('pfmp_user_code', None)
        request.session.pop('pfmp_auth_source', None)
        request.session.modified = True
    return user

def pfmp_context(request):
    return {
        'PFMP_APP_NAME': settings.PFMP_APP_NAME,
        'PFMP_VERSION': settings.PFMP_VERSION,
        'LP_CORE_PUBLIC_URL': settings.LP_CORE_PUBLIC_URL,
        'PFMP_PUBLIC_URL': settings.PFMP_PUBLIC_URL,
        'pfmp_current_user': current_pfmp_user(request),
    }
