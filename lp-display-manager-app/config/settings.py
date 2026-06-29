import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'lp-display-manager-dev-key-change-me')
DEBUG = os.getenv('DJANGO_DEBUG', '1') == '1'

ALLOWED_HOSTS = [h.strip() for h in os.getenv('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,*').split(',') if h.strip()]
CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.getenv('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]

BASE_PATH = os.getenv('LPDISPLAY_BASE_PATH', '/lpdisplaymanager').rstrip('/')
FORCE_SCRIPT_NAME = BASE_PATH
USE_X_FORWARDED_HOST = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'display_manager',
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

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'display_manager.context_processors.lpdisplay',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DB_ENGINE = os.getenv('LPDISPLAY_DB_ENGINE', 'sqlite')
if DB_ENGINE == 'postgres':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.getenv('LPDISPLAY_DB_NAME', 'lpdisplaymanager'),
            'USER': os.getenv('LPDISPLAY_DB_USER', 'lpdisplaymanager'),
            'PASSWORD': os.getenv('LPDISPLAY_DB_PASSWORD', ''),
            'HOST': os.getenv('LPDISPLAY_DB_HOST', 'db'),
            'PORT': os.getenv('LPDISPLAY_DB_PORT', '5432'),
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.getenv('LPDISPLAY_DB_NAME', str(BASE_DIR / 'data' / 'lpdisplaymanager.sqlite3')),
        }
    }

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True

STATIC_URL = f'{BASE_PATH}/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = f'{BASE_PATH}/uploads/'
MEDIA_ROOT = Path(os.getenv('LPDISPLAY_MEDIA_ROOT', str(BASE_DIR / 'media')))

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = f'{BASE_PATH}/login/'
SESSION_COOKIE_PATH = '/'
CSRF_COOKIE_PATH = '/'
X_FRAME_OPTIONS = 'SAMEORIGIN'

LPDISPLAY_OFFLINE_SECONDS = int(os.getenv('LPDISPLAY_OFFLINE_SECONDS', '90'))

LP_CORE_API_TOKEN = os.getenv('LP_CORE_API_TOKEN', '')
