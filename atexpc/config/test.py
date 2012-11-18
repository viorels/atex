import os

from atexpc.settings import *

DEBUG = False # test runner always sets this to False

SITE_ID = 3

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': '/tmp/atex.sql',
    }
}

INSTALLED_APPS += (
    'atexpc.ancora_api',
)

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'atex_web', 'media/')
MEDIA_URL = '/media/'
