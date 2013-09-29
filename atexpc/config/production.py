from os import path, environ
from urlparse import urlparse

from atexpc.settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

PREPEND_WWW = True

ALLOWED_HOSTS = [
    '.atexpc.ro',
    '.atexcomputer.ro',
]

MIDDLEWARE_CLASSES += (
    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware',
)

INSTALLED_APPS += (
    'gunicorn',
    'storages',
    'raven.contrib.django',
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

if environ.has_key('DATABASE_URL'):
    url = urlparse(environ['DATABASE_URL'])
    DATABASES = {'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': url.path[1:],
#        'USER': url.username,
#        'PASSWORD': url.password,
#        'HOST': url.hostname,
#        'PORT': url.port,
    }}
