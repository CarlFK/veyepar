#!/bin/bash -x

# clean up previous runs
# rm ~/Videos/veyepar/test_client/test_show/titles/Lets_make_a_Test.png
# rm -rf ~/Videos/veyepar/test_client/
# delete previous scripts
# rm ~/Videos/veyepar/test_client/test_show/tmp/Test_Episode.sh

# make files needed for testing:

# have something for post to post
# touch ~/Videos/veyepar/test_client/test_show/tmp/Test_Episode.sh

# rm ../veyepar.db
if [ ! -e ../veyepar.db ]; then
  ../manage.py syncdb --noinput
fi

# python run_tests.py --client test_client --show test_show -v --unlock --force
coverage run run_tests.py --client test_client --show test_show -v --unlock --force

# display ~/Videos/veyepar/test_client/test_show/titles/Lets_make_a_Test.png
