from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.getenv('TOOLMAG_DATA_DIR', BASE_DIR))
DATA_DIR.mkdir(parents=True, exist_ok=True)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'dev-only-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'inventory',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'toolmag.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {'context_processors': [
            'django.template.context_processors.debug',
            'django.template.context_processors.request',
            'django.contrib.auth.context_processors.auth',
            'django.contrib.messages.context_processors.messages',
            'inventory.context_processors.toolmag_context',
        ]},
    },
]

WSGI_APPLICATION = 'toolmag.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.getenv('DB_NAME', str(DATA_DIR / 'db.sqlite3')),
        'USER': os.getenv('DB_USER', ''),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', ''),
        'PORT': os.getenv('DB_PORT', ''),
        'CONN_MAX_AGE': int(os.getenv('DB_CONN_MAX_AGE', '60')),
    }
}

LANGUAGE_CODE = 'fr-fr'
LANGUAGES = [
    ('fr', 'Français'),
    ('en', 'English'),
]
LOCALE_PATHS = [BASE_DIR / 'locale']
LANGUAGE_COOKIE_NAME = 'toolmag_language'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = Path(os.getenv('STATIC_ROOT', DATA_DIR / 'staticfiles'))
MEDIA_URL = 'media/'
MEDIA_ROOT = Path(os.getenv('MEDIA_ROOT', DATA_DIR / 'media'))
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_URL = '/admin/login/'

# Base URL utilisée pour générer les QR codes imprimables en ligne de commande.
# En production : https://toolmag-atelier.duckdns.org
SERVER_IP = os.getenv('SERVER_IP', '192.168.104.15')
TOOLMAG_PORT = os.getenv('TOOLMAG_PORT', '9001')
LP_CORE_PORT = os.getenv('LP_CORE_PORT', '9000')
TOOLMAG_PUBLIC_BASE_URL = os.getenv('TOOLMAG_PUBLIC_BASE_URL', f'http://{SERVER_IP}:{TOOLMAG_PORT}').rstrip('/')
LP_CORE_API_URL = os.getenv('LP_CORE_API_URL', 'http://lp-core-app:8000').rstrip('/')
LP_CORE_PUBLIC_URL = os.getenv('LP_CORE_PUBLIC_URL', f'http://{SERVER_IP}:{LP_CORE_PORT}').rstrip('/')


# HTTPS / reverse proxy support
CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',') if origin]
LP_CORE_API_TOKEN = os.getenv('LP_CORE_API_TOKEN', 'dev-token-change-me')


# Static files served by WhiteNoise behind Gunicorn
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}



# Reverse proxy path-prefix support for lp-gateway.
APP_URL_PREFIX = os.getenv('APP_URL_PREFIX', '').strip().rstrip('/')
if APP_URL_PREFIX:
    FORCE_SCRIPT_NAME = APP_URL_PREFIX
    STATIC_URL = f'{APP_URL_PREFIX}/static/'
    MEDIA_URL = f'{APP_URL_PREFIX}/media/'
    SESSION_COOKIE_PATH = APP_URL_PREFIX + '/'
    CSRF_COOKIE_PATH = APP_URL_PREFIX + '/'
    LOGIN_URL = f'{APP_URL_PREFIX}/admin/login/'
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SESSION_COOKIE_SECURE = os.getenv('SESSION_COOKIE_SECURE', '0') == '1'
CSRF_COOKIE_SECURE = os.getenv('CSRF_COOKIE_SECURE', '0') == '1'

# HTTPS direct support. When Gunicorn serves TLS directly, cookies should be secure.
ENABLE_HTTPS = os.getenv('ENABLE_HTTPS', '0') == '1'
if ENABLE_HTTPS:
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

APP_VERSION = os.getenv('APP_VERSION', 'ToolMag — Bêta V0.2.0')


# --- LP SUITE UNIQUE MODULE COOKIES ---
SESSION_COOKIE_NAME = 'toolmag_sessionid'
CSRF_COOKIE_NAME = 'toolmag_csrftoken'
