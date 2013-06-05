#!/bin/bash -xe

# Usage:
# richard_quick.sh /path/to/richard package_name port fqdn

# Example:
# richard_quick.sh /srv/dev_pyvideo test_pyvideo 7000 anything.pyvideo.org
# richard_quick.sh /srv/psone psone 7001 video.pumpingstationone.org

SITE_ROOT="$1"
SITE_NAME="$(basename $SITE_ROOT)"

PACKAGE_NAME="$2"
GUNICORN_PORT="$3"
DOMAIN_NAME="$4"

if [ ! -d "$BASE_DIR" ] ; then
    sudo mkdir -p "$BASE_DIR"
    sudo chown -R $USER "$BASE_DIR"
fi

echo <<END_PSQL
Make the database user:
sudo -u postgres createuser -P $SITE_NAME

Make the database with:
sudo -u postgres createdb -O $SITE_NAME $SITE_NAME

Fix the password if needed:
sudo -u postgres psql -c "ALTER USER $SITE_NAME PASSWORD NEWPASSWORD"
END_PSQL
psql -P $PACKAGE_NAME $PACKAGE_NAME

pushd "$BASE_DIR" >/dev/null
git clone git://github.com/willkg/richard.git
mkdir -p document_root/static document_root/media config templates venv
virtualenv venv
source venv/bin/activate
pip install -r richard/requirements/base.html
pip install gunicorn
unlink venv/lib/python2.7/no-global-site-packages.txt

cat << 'PTH' > venv/lib/python2.7/site-packages/$SITE_NAME.pth
$SITE_ROOT/config
$SITE_ROOT/richard
PTH

cat << 'END_SUPERVISOR' > ${SITE_NAME}_supervisor.conf
[program:${PACKAGE_NAME}]
directory=${SITE_ROOT}
environment=DJANGO_SETTINGS_MODULE='${PACKAGE_NAME}_settings',VIRTUAL_ENV='${SITE_ROOT}/venv'
command=${SITE_ROOT}/venv/bin/gunicorn_django
        -w 2
        --log-level=debug
        --bind localhost:${GUNICORN_PORT}
autostart=false
autorestart=true
startsecs=3
startretries=3
user=$USER
group=$USER
stdout_logfile=/var/log/gunicorn/$DOMAIN_NAME.log
stderr_logfile=/var/log/gunicorn/${DOMAIN_NAME}_error.log
stdout_logfile_maxbytes=1MB
stderr_logfile_maxbytes=1MB
stdout_logfile_backups=10
stderr_logfile_backups=10
stopsignal=QUIT
END_SUPERVISOR

cat << 'END_NGINX' > ${SITE_NAME}_nginx.conf
server {
    listen 80;
    server_name ${DOMAIN_NAME};

    # no security problem here, since / is alway passed to upstream
    root ${SITE_ROOT}/document_root;
    # serve directly - analogous for static/staticfiles

    location /robots.txt {
        break;
    }

    location /favicon.ico {
        break;
    }

    location /static/ {
        break;
    }
    
    location / {
        proxy_pass_header     Server;
        proxy_set_header      Host               $http_host;
        proxy_set_header      X-Forwarded-Host   $host;
        proxy_set_header      X-Forwarded-Server $host;
        proxy_set_header      X-Real-IP          $remote_addr;
        proxy_set_header      X-Forwarded-For    $proxy_add_x_forwarded_for;
        proxy_set_header      X-Scheme           $scheme;
        proxy_redirect        off;
        proxy_connect_timeout 10;
        proxy_read_timeout    10;
        proxy_pass            http://localhost:${GUNICORN_PORT};
    }

    # what to serve if upstream is not available or crashes
    error_page 500 502 503 504 /media/50x.html;
}
END_NGINX

SECRET_KEY=$(python -c "from django.utils.crypto import get_random_string; chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'; print get_random_string(50, chars)")

cat << 'END_CONFIG' > ${PACKAGE_NAME}_settings.py
from richard.settings import *

import sys
import os

# site_root is the parent directory
SITE_ROOT = os.path.dirname(os.path.dirname(__file__))
DOCUMENT_ROOT = os.path.join(SITE_ROOT, 'document_root')

# root is this directory
ROOT = os.path.join(SITE_ROOT, 'richard', 'richard')

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SITE_URL = 'http://${DOMAIN_NAME}'

SITE_TITLE = u'${SITE_NAME} Videos'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

VIDEO_THUMBNAIL_SIZE = (160, 120)
MEDIA_PREFERENCE = ('ogv', 'webm', 'mp4')
API = True
AMARA_SUPPORT = False
PAGES = ['about']
MAX_FEED_LENGTH = 30

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql_psycopg2",
        "NAME": "${SITE_NAME}",
        "USER": "${SITE_NAME}",
        "PASSWORD": "${SITE_NAME}",
        "HOST": "127.0.0.1",
        "PORT": "",
    }
}

HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'haystack.backends.whoosh_backend.WhooshEngine',
        'PATH': os.path.join(SITE_ROOT, 'whoosh_index'),
    },
}

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = os.path.join(DOCUMENT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(DOCUMENT_ROOT, 'static')

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(SITE_ROOT, 'staticbase'),
    os.path.join(ROOT, 'base', 'static'),
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '${SECRET_KEY}'

TEMPLATE_DIRS = (
    os.path.join(SITE_ROOT, 'templates'),
    os.path.join(ROOT, 'templates'),
)

EMAIL_SUBJECT_PREFIX = '[Django %s] ' % SITE_TITLE

SPAM_WORDS = [
    'casino',
    'loans',
    'viagra',
    'valium',
    'proactol',
    'hormone',
    'forex',
    'cigarette',
    'cigarettes',
    'levitra',
    'blackjack',
    'poker',
    'cialis',
    'roulette',
    'propecia',
    'tramadol',
    'insurance',
    'payday',
    'keno',
    'hgh',
    'hair',
    'vegas',
    'ketone',
    'slots',
    'slot',
    'debt',
    'wartrol',
    'provestra',
    'bowtrol',
    'casinos',
    'loan',
    'pills',
    'diet',
    'hosting',
    'review',
    'repair',
    'toner',
    'party',
    'debt',
    'alarm',
    'locksmiths',
    ]

try:
    from ${PACKAGE_NAME}_settings_local import *
except ImportError:
    pass
END_CONFIG

cat << 'END_MANAGE_PY' > env/bin/manage.py
#!/usr/bin/env python
import os
import sys

if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "${PACKAGE_NAME}_settings")

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
END_MANAGE_PY
chmod u+x venv/bin/manage.py

manage.py validate
manage.py collectstatic --link --noinput
manage.py syncdb --noinput
manage.py migrate --noinput

popd
