#!/bin/bash -ex
# ins.sh - install encoder node

apt-get --assume-yes install software-properties-common

# http://ppa.launchpad.net/gstreamer-developers/ppa/ubuntu
sudo apt-add-repository --yes ppa:gstreamer-developers/ppa

sudo apt-get --assume-yes install \
    virtualenvwrapper python-pip python-psycopg2 \
    git-core vim screen tmux \
    imagemagick python-imaging inkscape ffmpeg2theora \
    python-gi python3-gi gstreamer1.0-tools gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 gstreamer1.0-plugins-good \
    python-numpy


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

