#!/bin/bash

set -e

SITE_VERSION={{ site_version }}
SITE_NAME={{ site_name }}
VIRTUALENV={{ site_home }}/venvs/$SITE_VERSION
SITE_ROOT={{ site_home }}/site
DJANGODIR=${SITE_ROOT}/{{ django_dir }}
PORT=8080
BIND_IP=127.0.0.1:$PORT
USER=`whoami`
GROUP=`whoami`
NUM_WORKERS=3
LOG_LEVEL=debug
DJANGO_WSGI_MODULE={{ wsgi_module }}

export DJANGO_SETTINGS_MODULE={{ django_settings_module }}
export PYTHONPATH=$DJANGODIR:$PYTHONPATH

echo "Starting $SITE_NAME version $SITE_VERSION as $USER using $VIRTUALENV"

cd $DJANGODIR

# Start your Django Unicorn
# Programs meant to be run under supervisor should not daemonize themselves (do not use --daemon)
exec ${VIRTUALENV}/bin/gunicorn ${DJANGO_WSGI_MODULE}:application \
  --name $SITE_NAME \
  --workers $NUM_WORKERS \
  --user=$USER \
  --group=$GROUP \
  --log-level=$LOG_LEVEL \
  --bind $BIND_IP
