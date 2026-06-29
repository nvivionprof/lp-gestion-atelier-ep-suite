from django.conf import settings


def lpdisplay(request):
    return {
        'LPDISPLAY_BASE_PATH': settings.FORCE_SCRIPT_NAME or '',
        'LPDISPLAY_APP_NAME': 'LP Display Manager',
    }
