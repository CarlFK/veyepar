#!/bin/bash -x

# updb.sh - update db
# pulls fairly recent data from production, loads it into the local db.
# uses a local file for auth
# so your user/pw will be what you created for your local dev db
# export it with:
# ./manage.py dumpdata auth > main/fixtures/veyepar_auth.json


if grep ^DATABASES dj/local_settings.py; then
    vim dj/local_settings.py
    exit
fi

# If the current user doesn't have ssh key access,
# BatchMode will cause this to fail and continue to the wget
ssh -o BatchMode=yes veyepar@veyepar.nextdayvideo.com /home/veyepar/site/veyepar/utils/dumpdata.sh


SRC=http://veyepar.nextdayvideo.com/temp
# wget -N $SRC/veyepar_all.json
# wget -N $SRC/veyepar_noauth.json
wget -N $SRC/veyepar_main.json
# wget -N $SRC/veyepar_auth.json

touch veyepar.db
mv  veyepar.db  ~/temp

python ./manage.py migrate --noinput
python ./manage.py loaddata veyepar_main.json
python ./manage.py loaddata veyepar_auth.json

# echo ./manage.py changepassword

# ./runsrv.sh
exit

