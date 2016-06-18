from os.path import abspath, dirname, join, normpath


SITE_ROOT = dirname(dirname(dirname(abspath(__file__))))
# STATIC_ROOT = normpath(join(dirname(SITE_ROOT), 'static'))
STATIC_ROOT = '{{ staticdir }}'
STATIC_URL = "/static/"
ADMIN_MEDIA_PREFIX = join(STATIC_URL, "admin/")

DATABASES =  {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'veyepar',
        'PORT': '5432', # TODO automate port change
    }
}
SECRET_KEY = '{{ secret_key }}'
