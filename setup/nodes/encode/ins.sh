#!/bin/bash -ex
# ins.sh - install encoder node

sudo apt-get --assume-yes install imagemagick python-imaging python-reportlab python-pip inkscape ffmpeg2theora git-core vim screen tmux virtualenvwrapper python-psycopg2

# sudo pip install hg+https://CarlFK@bitbucket.org/CarlFK/virtualenvwrapper

printf "\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc
source /usr/local/bin/virtualenvwrapper.sh

printf "workon veyepar\n" >> ~/.bashrc
mkvirtualenv --system-site-packages veyepar
# mkvirtualenv veyepar

workon veyepar
git clone git://github.com/CarlFK/veyepar.git
cd veyepar

pip install -r setup/requirements.txt

touch dj/dj/local_settings.py
touch dj/scripts/veyepar.cfg

