#!/bin/bash -xe

MLT_VER=$(melt --version 2>&1 | grep MLT)

if [ -e ../../bin/activate ]; then
 . ../../bin/activate
fi

rm -rf ~/Videos/veyepar/test_client/
rm ../veyepar.db
if [ ! -e ../veyepar.db ]; then
  ../manage.py syncdb --noinput
fi

python run_tests.py --client test_client --show test_show

