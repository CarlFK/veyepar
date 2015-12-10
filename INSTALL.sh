#!/bin/bash -xe
# Veyepar instalation script

# boot strap command to get this file and run it.
# wget --no-check-certificate -N http://github.com/CarlFK/veyepar/raw/master/INSTALL.sh
# chmod u+x INSTALL.sh

sudo apt-get --assume-yes install python

# install apt-add-repository:
sudo apt-get --assume-yes install python-software-properties
# sudo apt-get --assume-yes install software-properties-common

# trunk gstreamer - used for mkthumbs
# sudo apt-add-repository --yes ppa:gstreamer-developers/ppa

# sunab tracks melt trunk, 
# kxstudio has melt stable 
# sudo apt-add-repository ppa:sunab/kdenlive-svn
# sudo apt-add-repository ppa:kxstudio-team/ppa

# j^ theora dev ffmpeg2theora trunk
# http://ppa.launchpad.net/j/ppa/ubuntu/dists/
# sudo apt-add-repository --yes ppa:j/ppa

# I think this is an another melt source.
# sudo apt-add-repository ppa:freshmedia/ppa

# sudo apt-add-repository 'http://packages.medibuntu.org free non-free'

sudo apt-get --assume-yes update

sudo apt-get --assume-yes install python-gtk2 gocr imagemagick python-imaging python-reportlab python-pip mercurial subversion inkscape mplayer vlc git vim mencoder python-virtualenv sox python-dev python-gst-1.0 gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libav gir1.2-gstreamer-1.0

# Use Shotcut's melt for production,
# but install this for the test at the end of this script
sudo apt-get --assume-yes install melt

sudo apt-get --assume-yes install libyaml-dev libjpeg-dev

# python-gst0.10 gstreamer0.10-plugins-good gstreamer0.10-plugins-bad 
# python-lxml 
# python-dev libxml2-dev libxslt-dev
# sphinx2-bin 
# libavcodec-extra-52 libavdevice-extra-52 libavfilter-extra-1 libavformat-extra-52 libavutil-extra-50 libpostproc-extra-51 
# pocketsphinx-utils

# for encoder node
sudo apt-get --assume-yes install python-psycopg2 inkscape ffmpeg2theora python-imaging python-virtualenv 
# virtualenvwrapper 

sudo apt-get --assume-yes build-dep python-lxml python-psycopg2
# sudo apt-get build-dep python-opencv

# for web server 
# python-psycopg2 python-imaging python-virtualenv virtualenvwrapper 
# ttf-dejavu-core (for pdfs)

# gstreamer bindings
# apt-get install gir1.2-gst.* python-gobject # gobject-introspection
sudo apt-get --assume-yes install python-gi \
    gstreamer1.0-tools \
    gir1.2-gstreamer-1.0 \
    gir1.2-gst-plugins-base-1.0 \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-libav

# Why am I installing py3 stuff?
    # python3-gi \

# curl -s http://peak.telecommunity.com/dist/ez_setup.py | python - && easy_install pip && pip install -U pip virtualenv 

# sudo pip install hg+https://CarlFK@bitbucket.org/CarlFK/virtualenvwrapper
# sudo pip install hg+https://bitbucket.org/dhellmann/virtualenvwrapper

# printf "\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc
# source /usr/local/bin/virtualenvwrapper.sh 
# if [ ! -d ~/.virtualenvs ]; then
#   mkdir ~/.virtualenvs
#fi

# depending on which version of ve wrapper, need both to make sure:
# mkvirtualenv veyepar
# mkvirtualenv --system-site-packages veyepar
# printf "workon veyepar\n" >> ~/.bashrc

mkdir -p ~/.virtualenvs/
virtualenv ~/.virtualenvs/veyepar
printf "source  ~/.virtualenvs/veyepar/bin/activate\n" >> ~/.bashrc
source  ~/.virtualenvs/veyepar/bin/activate

if [ ! -d veyepar ]; then
  git clone git://github.com/CarlFK/veyepar.git
fi

cd veyepar

pip install -r setup/requirements.txt

# fix a bunch of things that don't pip install well
cd $(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")

# Dabo
# maybe it works now?  http://trac.dabodev.com/changeset/5554
# mv dabo/locale/ ./lib/python2.5/site-packages/dabo
# mv ~/.virtualenvs/veyepar/dabo/locale/ ~/.virtualenvs/veyepar/lib/python2.6/site-packages/dabo

git clone https://github.com/dabodev/dabo.git dabo-master
ln -s dabo-master/dabo 


ln -s /usr/lib/python2.7/dist-packages/gi

# to hookinto local open-cv
# python -c "import cv2;print cv2.__file__" 
# /usr/lib/python2.7/dist-packages/cv2.so
ln -s /usr/lib/python2.7/dist-packages/cv2.so

# python -c "import tesseract; print tesseract.__file__"
# /usr/lib/python2.7/dist-packages/tesseract.pyc
ln -s /usr/lib/python2.7/dist-packages/tesseract.pyc

# python -c "import _tesseract;print _tesseract.__file__"
# /usr/lib/python2.7/dist-packages/_tesseract.x86_64-linux-gnu.so
ln -s /usr/lib/python2.7/dist-packages/_tesseract.x86_64-linux-gnu.so

cd -

# grab some text files I don't want to check into the repo
cd dj/scripts
mkdir -p static
cd static
# wget -N http://0x80.org/wordlist/webster-dictionary.txt
# ln -s webster-dictionary.txt dictionary.txt


# removed because sphinx no longer installs - pulled from deb repos
# sox -b 16 -r 16k -e signed -c 1 -t raw \
#    /usr/share/sphinx2/model/lm/turtle/goforward.16k \
#    goforward.wav

cd ..
pwd
cp sample_pw.py pw.py
cp sample_veyepar.cfg veyepar.cfg
cd ../..

# either install apache or some other http server and figure out how to enable seeking in ogv, or allow file:// access to the local files:
# http://kb.mozillazine.org/Links_to_local_pages_do_not_work#Firefox_1.5.2C_SeaMonkey_1.0_and_newer  "Disabling the Security Check" 

# this assumes FireFox has been run, 
# which will create ~/.mozilla/firefox/profiles.ini

# This no longer works :(

# if [[ -f  ~/.mozilla/firefox/profiles.ini ]]; then 
#    python setup/nodes/review/set_ff_prefs.py
# fi

# adds these lines to FireFox config 
# user_pref("capability.policy.policynames", "localfilelinks");
# user_pref("capability.policy.localfilelinks.sites", "http://localhost:8080");
# user_pref("capability.policy.localfilelinks.checkloaduri.enabled", "allAccess");


echo INSTALL complte.
echo running tests...
cd dj/scripts
./rt.sh

