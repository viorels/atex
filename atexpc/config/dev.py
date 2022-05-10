import os

from atexpc.settings import *

DEBUG = True

ALLOWED_HOSTS = [
    'localhost',
]

INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}

SITE_ID = 1

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'atexdev',
    }
}

MIDDLEWARE += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
#    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
    'django_extensions',
)

COMPRESS_ENABLED = False

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'atex_web', 'media/')
MEDIA_URL = '/media/'

DEFAULT_FROM_EMAIL = SERVER_EMAIL = 'noreply@atexpc.ro'
EMAIL_SUBJECT_PREFIX = '[Atex dev] '
#EMAIL_HOST = 'gmail-smtp-in.l.google.com'
#EMAIL_PORT = 25
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

CACHES['default']['KEY_PREFIX'] = 'dev'
#CACHES['default']['BACKEND'] = 'django.core.cache.backends.dummy.DummyCache'
