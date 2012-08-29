#!/bin/bash -xe

# scp -P 222 veyepar@nextdayvideo.com:veyepar/dj/veyepar_all.json .
# scp -P 222 veyepar@nextdayvideo.com:veyepar/dj/veyepar_main.json .
# ./manage.py  dumpdata --settings dj.settings >vp_old.json 
touch veyepar.db 
rm veyepar.db 
./manage.py syncdb --noinput
./manage.py loaddata veyepar_main.json 
./manage.py loaddata veyepar_accounts.json
# accounts/fixtures/veyepar_auth.json
