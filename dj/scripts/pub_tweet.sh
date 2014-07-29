#!/bin/bash -xe

if grep ^DATABASES ../local_settings.py; then

/home/carl/.virtualenvs/veyepar/bin/python mk_public.py --unlock $*
/home/carl/.virtualenvs/veyepar/bin/python tweet.py $*

else
  vim ../local_settings.py
  exit
fi
