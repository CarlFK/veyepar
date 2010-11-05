#!/bin/bash -x
# Veyepar instalation notes

# install apt-add-repository:
sudo apt-get install python-software-properties

sudo apt-add-repository ppa:gstreamer-developers/ppa
sudo apt-add-repository ppa:sunab/kdenlive-svn
# sudo apt-add-repository ppa:j/ppa
# sudo apt-add-repository ppa:freshmedia/ppa

sudo apt-get update

sudo apt-get install gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gocr imagemagick python-imaging python-reportlab python-pip mercurial subversion inkscape melt ffmpeg2theora mplayer vlc git vim

sudo pip install hg+https://CarlFK@bitbucket.org/CarlFK/virtualenvwrapper
printf "\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc
source /usr/local/bin/virtualenvwrapper.sh 
# if [ ! -d ~/.virtualenvs ]; then
#   mkdir ~/.virtualenvs
#fi

mkvirtualenv veyepar
# workon veyepar

# git clone https://CarlFK@github.com/CarlFK/veyepar.git
# git clone git@github.com:CarlFK/veyepar.git
git clone git://github.com/CarlFK/veyepar.git

cd veyepar

# hg clone http://bitbucket.org/ianb/pip/
# cd pip/
# python setup.py install
# cd ..

pip install -r requirements.txt
# fix broken dabo installer
# mv dabo/locale/ ./lib/python2.5/site-packages/dabo
mv ~/.virtualenvs/veyepar/dabo/locale/ ~/.virtualenvs/veyepar/lib/python2.6/site-packages/dabo

# grab some text files I don't want to check into the repo
cd dj/scripts
mkdir static
cd static
wget -N http://0x80.org/wordlist/webster-dictionary.txt
ln -s webster-dictionary.txt dictionary.txt

cd ..
cp pw_samp.py pw.py
cp sample_veyepar.cfg veyepar.cfg
cd ../..

# either install apache or some other http server and figure out how to enable seeking in ogv, or allow file:// access to the local files:
# http://kb.mozillazine.org/Links_to_local_pages_do_not_work#Firefox_1.5.2C_SeaMonkey_1.0_and_newer  "Disabling the Security Check" 

python set_ff_prefs.py
# adds these lines to FireFox config 
# user_pref("capability.policy.policynames", "localfilelinks");
# user_pref("capability.policy.localfilelinks.sites", "http://localhost:8080");
# user_pref("capability.policy.localfilelinks.checkloaduri.enabled", "allAccess");

