import os

from atexpc.settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

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
        'NAME': 'atexpc',
    }
}

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
#    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware',
)

INSTALLED_APPS += (
    'debug_toolbar',
)

COMPRESS_ENABLED = False

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'atex_web', 'media/')
MEDIA_URL = '/media/'

SERVER_EMAIL = 'atex@durex.nul.ro'
EMAIL_SUBJECT_PREFIX = '[Atex dev] '
EMAIL_HOST = 'gmail-smtp-in.l.google.com'
