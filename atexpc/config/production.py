from os import path, environ
from urlparse import urlparse

from atexpc.settings import *

DEBUG = False
TEMPLATE_DEBUG = DEBUG

MIDDLEWARE_CLASSES += (
    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware',
)

INSTALLED_APPS += (
    'gunicorn',
    'storages',
)

COMPRESS_ENABLED = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = path.join(environ.get("HOME", ""), "media/")

SERVER_EMAIL = 'atex@atexsolutions.ro'
EMAIL_SUBJECT_PREFIX = '[Atex] '
EMAIL_HOST = 'gmail-smtp-in.l.google.com'

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
