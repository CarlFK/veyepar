#!/bin/bash -x

rm -rf ~/Videos/veyepar/test_client/
rm ../veyepar.db
if [ ! -e ../veyepar.db ]; then
  ../manage.py syncdb --noinput
fi

# delete previous scripts
rm ~/Videos/veyepar/test_client/test_show/tmp/Test_Episode.sh
# have something for post to post
touch ~/Videos/veyepar/test_client/test_show/tmp/Test_Episode.sh

python run_tests.py --client test_client --show test_show

