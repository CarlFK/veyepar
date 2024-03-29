#!/bin/bash -ex
# ins.sh - install encoder node

sudo apt-get --assume-yes install software-properties-common

# http://ppa.launchpad.net/gstreamer-developers/ppa/ubuntu
sudo apt-add-repository --yes ppa:gstreamer-developers/ppa

sudo apt-get --assume-yes install \
    virtualenvwrapper python-pip python-psycopg2 \
    git-core vim screen tmux \
    imagemagick python-imaging inkscape ffmpeg2theora \
    python-gi python3-gi gstreamer1.0-tools gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 gstreamer1.0-plugins-good \
    python-numpy

# sudo apt --assume-yes install python3-gi libgirepository1.0-dev
# pip install pycairo
# pip install PyGObject

# new stuff!!!
pip install pyocr
sudo apt install tesseract-ocr-eng tesseract-ocr



# sudo pip install hg+https://CarlFK@bitbucket.org/CarlFK/virtualenvwrapper

printf "\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc
source /usr/local/bin/virtualenvwrapper.sh

printf "workon veyepar\n" >> ~/.bashrc
mkvirtualenv --system-site-packages veyepar
# mkvirtualenv veyepar

workon veyepar
git clone git://github.com/CarlFK/veyepar.git
cd veyepar

pip install -r setup/nodes/encode/requirements.txt


# touch dj/dj/local_settings.py
# touch dj/scripts/veyepar.cfg
# 130.216.0.130:/mnt/barge      /home/av/Videos/veyepar    nfs     intr,soft,rsize=8192,wsize=8192,noauto,user 0       0


tmux new -s enc1

sudo vim /etc/resolv.conf
nameserver 8.8.8.8

wget --no-check-certificate -N http://github.com/CarlFK/veyepar/raw/master/INSTALL.sh ; chmod u+x INSTALL.sh ; ./INSTALL.sh

pip install psycopg2
sudo apt-get install sshfs
mkdir /home/av/Videos/veyepar/lca
sshfs av@130.216.0.130:/mnt/barge/lca/ /home/av/Videos/veyepar/lca
cp Videos/veyepar/lca/veyepar.cfg veyepar/dj/scripts/
cp Videos/veyepar/lca/local_settings.py veyepar/dj/dj
cd veyepar/dj/scripts/
python enc.py --poll 30
