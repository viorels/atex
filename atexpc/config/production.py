from os import path, environ
from urlparse import urlparse

DEBUG = True
TEMPLATE_DEBUG = DEBUG

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'atexpc.atex_web',
    'django.contrib.admin',
    'compressor',
    'gunicorn',
    'south',
    'storages',
    'sorl.thumbnail',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_ENABLED = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = path.join(environ.get("HOME", ""), "media/")

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
