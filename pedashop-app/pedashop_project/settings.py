"""Configuration Django du module PedaShop.

PedaShop est un module séparé : il possède son conteneur, sa base SQLite et
ses fichiers statiques/médias. Il ne lit pas directement la base LP Core.
Les utilisateurs sont synchronisés via l’API interne LP Core, comme ToolMag.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv('PEDASHOP_DATA_DIR', BASE_DIR / 'data'))
DATA_DIR.mkdir(parents=True, exist_ok=True)

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-change-me-pedashop')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')
CSRF_TRUSTED_ORIGINS = [x for x in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if x]

INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'pedashop',
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

ROOT_URLCONF = 'pedashop_project.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'pedashop.context_processors.pedashop_context',
    ]},
}]
WSGI_APPLICATION = 'pedashop_project.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', str(DATA_DIR / 'pedashop.sqlite3')),
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

SERVER_IP = os.getenv('SERVER_IP', 'localhost')
LP_CORE_PORT = os.getenv('LP_CORE_PORT', '9000')
TOOLMAG_PORT = os.getenv('TOOLMAG_PORT', '9001')
SAFETY_PORT = os.getenv('SAFETY_PORT', '9002')
PEDASHOP_PORT = os.getenv('PEDASHOP_PORT', os.getenv('CONSUMABLES_PORT', '9003'))
INVENTORY_PORT = os.getenv('INVENTORY_PORT', '9004')
TPMANAGER_PORT = os.getenv('TPMANAGER_PORT', '9005')

LP_CORE_PUBLIC_URL = os.getenv('LP_CORE_PUBLIC_URL', f'http://{SERVER_IP}:{LP_CORE_PORT}').rstrip('/')
TOOLMAG_PUBLIC_BASE_URL = os.getenv('TOOLMAG_PUBLIC_BASE_URL', f'http://{SERVER_IP}:{TOOLMAG_PORT}').rstrip('/')
SAFETY_PUBLIC_URL = os.getenv('SAFETY_PUBLIC_URL', f'http://{SERVER_IP}:{SAFETY_PORT}').rstrip('/')
PEDASHOP_PUBLIC_URL = os.getenv('PEDASHOP_PUBLIC_URL', os.getenv('CONSUMABLES_PUBLIC_URL', f'http://{SERVER_IP}:{PEDASHOP_PORT}')).rstrip('/')

LP_CORE_API_URL = os.getenv('LP_CORE_API_URL', 'http://lp-core-app:8000').rstrip('/')
LP_CORE_API_TOKEN = os.getenv('LP_CORE_API_TOKEN', '')
PEDASHOP_APP_NAME = os.getenv('PEDASHOP_APP_NAME', 'PedaShop')
PEDASHOP_VERSION = os.getenv('PEDASHOP_VERSION', 'PedaShop — Bêta V0.2.0')

# Cookies isolés par application : évite les collisions entre modules servis sous le même domaine.
SESSION_COOKIE_NAME = os.getenv('PEDASHOP_SESSION_COOKIE_NAME', 'pedashop_sessionid')
CSRF_COOKIE_NAME = os.getenv('PEDASHOP_CSRF_COOKIE_NAME', 'pedashop_csrftoken')
SESSION_COOKIE_SAMESITE = os.getenv('SESSION_COOKIE_SAMESITE', 'Lax')
CSRF_COOKIE_SAMESITE = os.getenv('CSRF_COOKIE_SAMESITE', 'Lax')

PEDASHOP_RESET_PASSWORDS_ON_SYNC = os.getenv('PEDASHOP_RESET_PASSWORDS_ON_SYNC', '0') == '1'




# Reverse proxy path-prefix support for lp-gateway.
APP_URL_PREFIX = os.getenv('APP_URL_PREFIX', '').strip().rstrip('/')
if APP_URL_PREFIX:
    FORCE_SCRIPT_NAME = APP_URL_PREFIX
    STATIC_URL = f'{APP_URL_PREFIX}/static/'
    MEDIA_URL = f'{APP_URL_PREFIX}/media/'
    SESSION_COOKIE_PATH = APP_URL_PREFIX + '/'
    CSRF_COOKIE_PATH = APP_URL_PREFIX + '/'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', '0') == '1'

# HTTPS direct support. When Gunicorn serves TLS directly, cookies should be secure.
ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', '0') == '1'
if ENABLE_HTTPS:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
