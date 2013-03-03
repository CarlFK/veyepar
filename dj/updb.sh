#!/bin/bash -xe

if grep ^DATABASES local_settings.py; then
    vim local_settings.py
    exit
fi

ssh -p 222 veyepar@nextdayvideo.com /home/veyepar/veyepar/dj/dumpdata.sh

# scp -P 222 veyepar@nextdayvideo.com:veyepar/dj/veyepar_main.json .
wget -N http://veyepar.nextdayvideo.com/site_media/static/veyepar/db/veyepar_main.json

touch dj/veyepar.db 
mv  dj/veyepar.db  ~/temp

./manage.py syncdb --noinput
./manage.py loaddata veyepar_main.json 
./manage.py loaddata veyepar_accounts.json
# ./runsrv.sh
