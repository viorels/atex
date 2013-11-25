import os

from atexpc.settings import *

INTERNAL_IPS = os.environ.get('DEBUG_IPS', '').split(',')

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'atexpc.atex_web.tools.dynamicsite.DynamicSiteIDMiddleware',
)

INSTALLED_APPS += (
    'gunicorn',
    'storages',
    'debug_toolbar',
)

COMPRESS_ENABLED = True

STATICFILES_STORAGE = 'storages.backends.s3boto.S3BotoStorage'
DEFAULT_FILE_STORAGE = STATICFILES_STORAGE
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
AWS_STORAGE_BUCKET_NAME = "dev.atexpc.ro"

STATIC_URL = "http://%s.s3-website-eu-west-1.amazonaws.com/" % AWS_STORAGE_BUCKET_NAME
MEDIA_URL = STATIC_URL

env[MEMCACHE_SERVERS] = env[MEMCACHIER_SERVERS]
env[MEMCACHE_USERNAME] = env[MEMCACHIER_USERNAME]
env[MEMCACHE_PASSWORD] = env[MEMCACHIER_PASSWORD]

