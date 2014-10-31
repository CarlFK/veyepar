#!/bin/bash -x

# updb.sh - update db
# pulls fairly recent data from production,
# uses a local file for auth 
# so your user/pw will be what you created for your local dev db
# export it with:
# ./manage.py dumpdata auth > main/fixtures/veyepar_auth.json


if grep ^DATABASES local_settings.py; then
    vim local_settings.py
    exit
fi

# If the current user doesn't have ssh key access, 
# BatchMode will cause this to fail and continue to the wget
ssh -o BatchMode=yes veyepar@veyepar.nextdayvideo.com /home/veyepar/site/veyepar/utils/dumpdata.sh

SRC=http://veyepar.nextdayvideo.com/static/temp
# wget -N $SRC/veyepar_all.json
# wget -N $SRC/veyepar_noauth.json
wget -N $SRC/veyepar_main.json
# wget -N $SRC/veyepar_auth.json

touch veyepar.db 
mv  veyepar.db  ~/temp

python ./manage.py syncdb --noinput
python ./manage.py loaddata veyepar_main.json 
# python ./manage.py loaddata veyepar_auth.json

# echo ./manage.py changepassword

# ./runsrv.sh
exit

alter table main_show add conf_url varchar(200);
alter table main_episode add priority integer,;
alter table main_episode add "conf_meta" text;
alter table main_episode add "twitter_id" varchar(50);
alter table main_episode add "language" varchar(20);
alter table main_episode add "summary" text;
alter table main_episode add ;

priority" integer,
103a106
>     "conf_meta" text NOT NULL,
105a109,110
>     "twitter_id" varchar(135) NOT NULL,
>     "language" varchar(20) NOT NULL,
106a112
>     "summary" text NOT NULL,
