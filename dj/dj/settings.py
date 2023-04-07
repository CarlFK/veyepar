# Django settings for veyepar project.

import os

DEBUG = True

BASE_DIR = os.path.dirname( os.path.dirname(
        os.path.abspath(__file__)))
# this file is down a level, so the base is the parent dir.
# PROJECT_ROOT = os.path.abspath(os.path.dirname(__file__))
        # os.path.dirname(os.path.dirname(__file__)))

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

# STATICFILES_DIRS = [os.path.expanduser('~/Videos/veyepar'),]
STATIC_URL = "/static/"

MEDIA_URL = "https://veyepar.nextdayvideo.com/Videos/veyepar/"

UPLOAD_FORMATS = ['mp4',]

MANAGERS = ADMINS
DATABASES =  {'default': {'ENGINE': 'django.db.backends.sqlite3',
 'HOST': '',
 'NAME': os.path.join(BASE_DIR,'veyepar.db'),
 'OPTIONS': {},
 'PASSWORD': '',
 'PORT': '',
 'TEST_CHARSET': None,
 'TEST_COLLATION': None,
 'TEST_NAME': None,
 'USER': ''} }

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
# TIME_ZONE = 'America/Chicago'
# TIME_ZONE = 'Australia/Hobart'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

# SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
# MEDIA_ROOT = os.path.expanduser('~/Videos/veyepar')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
# MEDIA_URL = '/static'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
# ADMIN_MEDIA_PREFIX = '/static/admin/'
ADMIN_MEDIA_PREFIX = STATIC_URL + 'admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '_)n%2id#&ke+^q_si_9c^v(+d9o6$&6kp*&s*w2sl$%esyx4$v'

LOGIN_URL = '/accounts/login'
# LOGIN_REDIRECT_URL = '/main'

xTEMPLATE_CONTEXT_PROCESSORS = (
    # 'django.core.context_processors.auth',
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.request',
    )

# List of callables that know how to import templates from various sources.
xTEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader'
)

xTEMPLATE_DEBUG = DEBUG
xTEMPLATE_STRING_IF_INVALID = 'template_error'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            # insert your TEMPLATE_DIRS here
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                # Insert your TEMPLATE_CONTEXT_PROCESSORS here or use this
                # list if you haven't customized them:
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
            ],
           'debug':DEBUG,
           'string_if_invalid':'error-in-template',
        },
    },
]

MIDDLEWARE = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.middleware.common.CommonMiddleware',
)

VALIDATOR_APP_VALIDATORS = {
        'text/html': '/usr/bin/validate',
        'application/xml+xhtml': '/usr/bin/validate',
    }
if DEBUG:
    INTERNAL_IPS = ('127.0.0.1',)
    MIDDLEWARE = \
        (
        # 'lukeplant_me_uk.django.validator.middleware.ValidatorMiddleware',
        # 'debug_toolbar.middleware.DebugToolbarMiddleware',
                ) +\
        MIDDLEWARE

ROOT_URLCONF = 'dj.urls'

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
     # 'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.staticfiles',
    'main',
    'accounts',
    'volunteers',
    'rest_framework',
    'api',
    'django_extensions',
    # "debug_toolbar",
    # 'django_databrowse',
)

REST_FRAMEWORK = {
    # Use hyperlinked styles by default.
    # Only used if the `serializer_class` attribute is not set on a view.
    'DEFAULT_MODEL_SERIALIZER_CLASS':
        'rest_framework.serializers.HyperlinkedModelSerializer',

    # Use Django's standard `django.contrib.auth` permissions,
    # or allow read-only access for unauthenticated users.
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'
    ]
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

try:    from dj.local_settings import *
except ImportError:    pass

