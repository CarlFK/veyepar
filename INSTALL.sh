#!/bin/bash -x
# Veyepar instalation script

# boot strap command to get this file and run it.
# wget -N http://github.com/CarlFK/veyepar/raw/master/INSTALL.sh
# chmod u+x INSTALL.sh

# install apt-add-repository:
sudo apt-get --assume-yes install python-software-properties

# trunk gstreamer - used for mkthumbs
sudo apt-add-repository --yes ppa:gstreamer-developers/ppa

# sunab tracks melt trunk, 
# kxstudio has melt stable 
# sudo apt-add-repository ppa:sunab/kdenlive-svn
# sudo apt-add-repository ppa:kxstudio-team/ppa

# j^ theora dev ffmpeg2theora trunk
# http://ppa.launchpad.net/j/ppa/ubuntu/dists/
sudo apt-add-repository --yes ppa:j/ppa
# sudo apt-add-repository 'deb http://ppa.launchpad.net/j/ppa/ubuntu maverick main'

# I think this is an another melt source.
# sudo apt-add-repository ppa:freshmedia/ppa

# sudo apt-add-repository 'deb http://packages.medibuntu.org/ '$(lsb_release -cs)' free non-free'
# once natty is released:
# sudo apt-add-repository 'http://packages.medibuntu.org free non-free'

sudo apt-get --assume-yes update

sudo apt-get --assume-yes install python-gtk2 python-gst0.10 gstreamer0.10-plugins-good gstreamer0.10-plugins-bad gocr imagemagick python-imaging python-reportlab python-pip mercurial subversion inkscape ffmpeg2theora mplayer vlc git vim mencoder ffmpeg python-virtualenv screen sox melt 
# sphinx2-bin 
# libavcodec-extra-52 libavdevice-extra-52 libavfilter-extra-1 libavformat-extra-52 libavutil-extra-50 libpostproc-extra-51 
# pocketsphinx-utils

# for encoder node
# python-psycopg2 inkscape ffmpeg2theora python-imaging python-virtualenv virtualenvwrapper

# for web server 
# python-psycopg2 python-imaging python-virtualenv virtualenvwrapper 
# ttf-dejavu-core (for pdfs)


# curl -s http://peak.telecommunity.com/dist/ez_setup.py | python - && easy_install pip && pip install -U pip virtualenv 

sudo pip install hg+https://CarlFK@bitbucket.org/CarlFK/virtualenvwrapper
# sudo pip install hg+https://bitbucket.org/dhellmann/virtualenvwrapper

printf "\nsource /usr/local/bin/virtualenvwrapper.sh\n" >> ~/.bashrc
source /usr/local/bin/virtualenvwrapper.sh 
# if [ ! -d ~/.virtualenvs ]; then
#   mkdir ~/.virtualenvs
#fi

# depending on which version of ve wrapper, need both to make sure:
mkvirtualenv veyepar
mkvirtualenv --system-site-packages veyepar
printf "workon veyepar\n" >> ~/.bashrc

git clone git://github.com/CarlFK/veyepar.git

cd veyepar

pip install -r requirements.txt
# fix broken dabo installer
# mv dabo/locale/ ./lib/python2.5/site-packages/dabo
# mv ~/.virtualenvs/veyepar/dabo/locale/ ~/.virtualenvs/veyepar/lib/python2.6/site-packages/dabo
cd $(python -c "from distutils.sysconfig import get_python_lib; print get_python_lib()")
# svn checkout http://svn.dabodev.com/dabo/trunk dabo-svn
# ln -s dabo-svn/dabo 
git clone git@github.com:dabodev/dabo.git dabo-master
ln -s dabo-master/dabo 
cd -

# grab some text files I don't want to check into the repo
cd dj/scripts
mkdir static
cd static
wget -N http://0x80.org/wordlist/webster-dictionary.txt
ln -s webster-dictionary.txt dictionary.txt

wget https://www.dropbox.com/sh/02zhv4v7lrdzmmg/W3Jqcs25HK/Synthview%20-%20Novecentowide-Bold.otf
wget https://www.dropbox.com/sh/02zhv4v7lrdzmmg/imS01PwStJ/Synthview%20-%20Novecentowide-Light.otf
mv *.otf ~/.fonts/

# removed because sphinx no longer installs - pulled from deb repos
# sox -b 16 -r 16k -e signed -c 1 -t raw \
#    /usr/share/sphinx2/model/lm/turtle/goforward.16k \
#    goforward.wav

cd ..
cp sample_pw.py pw.py
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

