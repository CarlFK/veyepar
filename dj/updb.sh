#!/bin/bash -xe

ssh -p 222 veyepar@nextdayvideo.com /home/veyepar/veyepar/dj/dumpdata.sh

scp -P 222 veyepar@nextdayvideo.com:veyepar/dj/veyepar_main.json .
# ./manage.py  dumpdata --settings dj.settings >vp_old.json 
touch veyepar.db 
mv  veyepar.db  ~/temp

# workon veyepar
./manage.py syncdb --noinput
./manage.py loaddata veyepar_main.json 
./manage.py loaddata veyepar_accounts.json
# ./runsrv.sh
