#!/bin/bash -x
# Veyepar instalation script

# wget --no-check-certificate https://github.com/CarlFK/veyepar/raw/master/INSTALL.sh
# chmod u+x INSTALL.sh

# install apt-add-repository:
sudo apt-get install python-software-properties

sudo apt-add-repository ppa:gstreamer-developers/ppa
sudo apt-add-repository ppa:sunab/kdenlive-svn
# sudo apt-add-repository ppa:j/ppa
# sudo apt-add-repository ppa:freshmedia/ppa

sudo apt-add-repository 'deb http://packages.medibuntu.org/ '$(lsb_release -cs)' free non-free'

sudo apt-get update

sudo apt-get install python-gtk2 python-gst0.10 gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gocr imagemagick python-imaging python-reportlab python-pip mercurial subversion inkscape melt ffmpeg2theora mplayer vlc git vim python-virtualenv  libavcodec-extra-52 libavdevice-extra-52 libavfilter-extra-1 libavformat-extra-52 libavutil-extra-50 libpostproc-extra-51 mencoder ffmpeg

sudo pip install hg+https://CarlFK@bitbucket.org/CarlFK/virtualenvwrapper
printf "\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc
source /usr/local/bin/virtualenvwrapper.sh 
# if [ ! -d ~/.virtualenvs ]; then
#   mkdir ~/.virtualenvs
#fi

mkvirtualenv veyepar
printf "workon veyepar\n" >> ~/.bashrc

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
# mv ~/.virtualenvs/veyepar/dabo/locale/ ~/.virtualenvs/veyepar/lib/python2.6/site-packages/dabo
cd $(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
svn checkout http://svn.dabodev.com/dabo/trunk dabo-svn
ln -s dabo-svn/dabo 
cd -

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

# this assumes FireFox has been run, 
# which will create ~/.mozilla/firefox/profiles.ini
if [[ -f  ~/.mozilla/firefox/profiles.ini ]]; then 
    python set_ff_prefs.py
# adds these lines to FireFox config 
# user_pref("capability.policy.policynames", "localfilelinks");
# user_pref("capability.policy.localfilelinks.sites", "http://localhost:8080");
# user_pref("capability.policy.localfilelinks.checkloaduri.enabled", "allAccess");
fi

echo INSTALL complte.
echo running tests...
cd dj/scripts
./rt.sh

