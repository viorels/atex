from os import path, environ
import sys

# Django settings for atexpc project.

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Viorel Stirbu', 'viorels@gmail.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
    # XXX: overridden by environment specific file in "config" directory
}

PROJECT_ROOT = path.dirname(path.realpath(__file__))

ANCORA_URI = environ.get('ANCORA_URI')

DROPBOX_APP_KEY = environ.get('DROPBOX_APP_KEY')
DROPBOX_APP_SECRET = environ.get('DROPBOX_APP_SECRET')
DROPBOX_ACCESS_TYPE = environ.get('DROPBOX_ACCESS_TYPE', 'dropbox')
DROPBOX_ACCESS_TOKEN = environ.get('DROPBOX_ACCESS_TOKEN')
DROPBOX_ACCESS_TOKEN_SECRET = environ.get('DROPBOX_ACCESS_TOKEN_SECRET')

AUTH_USER_MODEL = 'atex_web.CustomUser'
SOCIAL_AUTH_USER_MODEL = 'atex_web.CustomUser'
INITIAL_CUSTOM_USER_MIGRATION = '0020_drop_customuser_username.py'

SHOPMANIA_FEED_FILE = 'shopmania.csv'   # in media root

if 'test' in sys.argv:
    DATABASES['default']['ENGINE'] = 'django.db.backends.sqlite3'


CACHES = {
    'default': {
        'BACKEND': 'django_pylibmc.memcached.PyLibMCCache',
        'TIMEOUT': 300,
    }
}

AUTHENTICATION_BACKENDS = (
    'social_auth.backends.google.GoogleOAuth2Backend',
    'social_auth.backends.contrib.yahoo.YahooOAuthBackend',
    'social_auth.backends.facebook.FacebookBackend',
    'django.contrib.auth.backends.ModelBackend',
    'atexpc.atex_web.ancora_api.AncoraAuthBackend'
)

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = '/'

GOOGLE_OAUTH2_CLIENT_ID = environ.get('GOOGLE_OAUTH2_CLIENT_ID')
GOOGLE_OAUTH2_CLIENT_SECRET = environ.get('GOOGLE_OAUTH2_CLIENT_SECRET')
YAHOO_CONSUMER_KEY = environ.get('YAHOO_CONSUMER_KEY')
YAHOO_CONSUMER_SECRET = environ.get('YAHOO_CONSUMER_SECRET')
FACEBOOK_APP_ID = environ.get('FACEBOOK_APP_ID')
FACEBOOK_API_SECRET = environ.get('FACEBOOK_API_SECRET')

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Bucharest'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path.join(PROJECT_ROOT, 'atex_web', 'static/')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
    
    'compressor.finders.CompressorFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '^phe(gn-&amp;laaufa=o_f90ulmmqd1@6yj7sslxq62z@&amp;m8-(ab*'
PASSWORD_SALT = '$2a$12$LtYdysZjnWn1w39ydF/bVe'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
)

ROOT_URLCONF = 'atexpc.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'atexpc.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path.join(PROJECT_ROOT, 'templates'),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    
    'django.contrib.redirects',
    'compressor',
    'south',
    'sorl.thumbnail',
    'social_auth',
    'atexpc.atex_web',
)

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'null': {
            'level':'DEBUG',
            'class':'django.utils.log.NullHandler',
        },
        'console':{
            'level':'DEBUG',
            'class':'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True
        }
    },
    'loggers': {
        'django': {
            'handlers':['console'],
            'propagate': True,
            'level':'INFO',
        },
        'django.request': {
            'handlers': [],
            'level': 'ERROR',
            'propagate': True,
        },
        'atexpc.atex_web': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'atexpc.ancora_api': {
            'handlers': ['console'],
            'level': 'DEBUG',
        }
    }
}

if environ.get('DJANGO_SETTINGS_MODULE').endswith('settings'):
    raise Exception("DJANGO_SETTINGS_MODULE must be set to environment specific value, "
                    "e.g. 'atexpc.config.production'")
