from django.conf import settings

CONSUMER_KEY = getattr(settings, 'DROPBOX_APP_KEY', None)
CONSUMER_SECRET = getattr(settings, 'DROPBOX_APP_SECRET', None)
ACCESS_TOKEN = getattr(settings, 'DROPBOX_ACCESS_TOKEN', None)
ACCESS_TOKEN_SECRET = getattr(settings, 'DROPBOX_ACCESS_TOKEN_SECRET', None)
ACCESS_TYPE = getattr(settings, 'DROPBOX_ACCESS_TYPE', 'app_folder')

