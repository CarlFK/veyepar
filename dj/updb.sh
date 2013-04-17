#!/bin/bash -x

# updb.sh - update db
# pulls fairly recent data from production,
# uses a local file for auth 
# so your user/pw will be what you created for your local dev db
# export it with:
# ./manage.py dumpdata auth > veyepar_auth.json
# ./manage.py dumpdata auth > main/fixtures/veyepar_auth.json


if grep ^DATABASES local_settings.py; then
    vim local_settings.py
    exit
fi

# If the current user doesn't have ssh key access, 
# BatchMode will cause this to fail and continue to the wget
ssh -o BatchMode=yes -p 222 veyepar@nextdayvideo.com /home/veyepar/veyepar/dj/dumpdata.sh

wget -N http://veyepar.nextdayvideo.com/site_media/static/veyepar/db/veyepar_main.json

touch veyepar.db 
mv  veyepar.db  ~/temp

./manage.py syncdb --noinput
./manage.py loaddata veyepar_main.json 
./manage.py loaddata veyepar_auth.json
# ./manage.py changepassword

# ./runsrv.sh
