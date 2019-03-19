#!/bin/bash -xe

if grep ^DATABASES ../dj/local_settings.py; then

python mk_public.py --unlock $*
python tweet.py $*
python email_conf.py $*

else
  vim ../local_settings.py
  exit
fi
