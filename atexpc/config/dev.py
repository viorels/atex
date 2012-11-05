import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

INTERNAL_IPS = ('127.0.0.1',)
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False
}

SITE_ID = 1

CONFIG_PATH = os.path.dirname(os.path.realpath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(CONFIG_PATH, os.pardir))

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'atexpc',
    }
}

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',

    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
#    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    'django.contrib.admin',
    'django.contrib.redirects',
    'compressor',
    'south',
#    'storages',
    'sorl.thumbnail',
    'debug_toolbar',
    'atexpc.atex_web',
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'compressor.finders.CompressorFinder',
)

COMPRESS_ENABLED = False

# STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
# DEFAULT_FILE_STORAGE = STATICFILES_STORAGE
# AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
# AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
# AWS_STORAGE_BUCKET_NAME = "dev.atexpc.ro"

MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'atex_web', 'media/')

MEDIA_URL = '/media/'
#MEDIA_URL = "http://%s.s3-website-eu-west-1.amazonaws.com/" % AWS_STORAGE_BUCKET_NAME

SERVER_EMAIL = 'atex@durex.nul.ro'
EMAIL_SUBJECT_PREFIX = '[Atex dev] '
EMAIL_HOST = 'gmail-smtp-in.l.google.com'
