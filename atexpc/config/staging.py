from os import path, environ
from urllib.parse import urlparse

from atexpc.settings import *

DEBUG = True

PREPEND_WWW = True

ALLOWED_HOSTS = [
    '.atexpc.ro',
    '.atexcomputer.ro',
]

MIDDLEWARE_CLASSES += (
    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware',
)

INSTALLED_APPS += (
    'storages',
)

COMPRESS_ENABLED = True

SENTRY_DSN = environ.get('SENTRY_DSN')

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = path.join(environ.get("HOME", ""), "media/")

DEFAULT_FROM_EMAIL = SERVER_EMAIL = '"ATEX Computer" <noreply@atexpc.ro>'
EMAIL_SUBJECT_PREFIX = '[Atex] '
EMAIL_HOST = 'localhost'
EMAIL_PORT = 25

if 'DATABASE_URL' in environ:
    url = urlparse(environ['DATABASE_URL'])
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
#        'USER': url.username,
#        'PASSWORD': url.password,
#        'HOST': url.hostname,
#        'PORT': url.port,
    }}

CACHES['default']['OPTIONS']['DB'] = 1
CACHES['default']['KEY_PREFIX'] = 'staging'

BROKER_URL = 'redis://localhost:6379/1'
CELERY_RESULT_BACKEND = BROKER_URL
