from pathlib import Path
import os
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv('PFMP_DATA_DIR', BASE_DIR / 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-change-me-pfmp')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = [x for x in os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',') if x]

def _origin(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f'{parsed.scheme}://{parsed.netloc}'
    except Exception:
        pass
    return ''

SERVER_IP = os.getenv('SERVER_IP', 'localhost')
LP_CORE_PORT = os.getenv('LP_CORE_PORT', '9000')
LP_CORE_PUBLIC_URL = os.getenv('LP_CORE_PUBLIC_URL', f'http://{SERVER_IP}:{LP_CORE_PORT}').rstrip('/')
PFMP_PUBLIC_URL = os.getenv('PFMP_PUBLIC_URL', f'{LP_CORE_PUBLIC_URL}/pfmp/').rstrip('/')

_csrf = [x for x in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if x]
for _candidate in (_origin(LP_CORE_PUBLIC_URL), _origin(PFMP_PUBLIC_URL)):
    if _candidate and _candidate not in _csrf:
        _csrf.append(_candidate)
CSRF_TRUSTED_ORIGINS = _csrf

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'pfmp_manager',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'pfmp_project.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'pfmp_manager.context_processors.pfmp_context',
    ]},
}]
WSGI_APPLICATION = 'pfmp_project.wsgi.application'
DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', str(DATA_DIR / 'pfmp-manager.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
    }
}

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True
STATIC_URL = '/static/'
STATIC_ROOT = Path(os.getenv('STATIC_ROOT', DATA_DIR / 'staticfiles'))
MEDIA_URL = '/media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', DATA_DIR / 'media'))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
}

LP_CORE_API_URL = os.getenv('LP_CORE_API_URL', 'http://lp-core-app:8000').rstrip('/')
LP_CORE_API_TOKEN = os.getenv('LP_CORE_API_TOKEN', 'dev-token-change-me')
PFMP_APP_NAME = os.getenv('PFMP_APP_NAME', 'PFMP Manager')
PFMP_VERSION = os.getenv('PFMP_VERSION', 'PFMP Manager — Bêta V0.3.1 hotfix')
PFMP_RESET_PASSWORDS_ON_SYNC = os.getenv('PFMP_RESET_PASSWORDS_ON_SYNC', '0') == '1'
PFMP_SSO_TOKEN_MAX_AGE = int(os.getenv('PFMP_SSO_TOKEN_MAX_AGE', '600'))

# Reverse proxy path-prefix support for lp-gateway.
APP_URL_PREFIX = os.getenv('APP_URL_PREFIX', '').strip().rstrip('/')
if APP_URL_PREFIX:
    FORCE_SCRIPT_NAME = APP_URL_PREFIX
    STATIC_URL = f'{APP_URL_PREFIX}/static/'
    MEDIA_URL = f'{APP_URL_PREFIX}/media/'
    SESSION_COOKIE_PATH = APP_URL_PREFIX + '/'
    CSRF_COOKIE_PATH = APP_URL_PREFIX + '/'

# Cookies isolés : PFMP ne doit jamais réutiliser le cookie sessionid de LP Core ou d'un autre module.
SESSION_COOKIE_NAME = os.getenv('PFMP_SESSION_COOKIE_NAME', 'pfmp_sessionid')
CSRF_COOKIE_NAME = os.getenv('PFMP_CSRF_COOKIE_NAME', 'pfmp_csrftoken')
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')
SESSION_SAVE_EVERY_REQUEST = os.getenv('SESSION_SAVE_EVERY_REQUEST', '0') == '1'

USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', '0') == '1'
ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', '0') == '1'
if ENABLE_HTTPS:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
