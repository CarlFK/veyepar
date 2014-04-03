#!/bin/bash -x

sudo apt-add-repository multiverse
sudo apt-get --assume-yes install libphonon-dev phonon-backend-gstreamer
sudo apt-get --assume-yes install git automake autoconf libtool intltool g++ yasm swig libmp3lame-dev libgavl-dev libsamplerate-dev libxml2-dev ladspa-sdk libjack-dev libsox-dev libsdl-dev libgtk2.0-dev liboil-dev libsoup2.4-dev libqt4-dev libexif-dev libtheora-dev libvdpau-dev libvorbis-dev python-dev kdelibs5-dev cmake libvpx-dev libfaac-dev libeigen3-dev libglew-dev

mkdir -p melt
cd melt
wget -N https://raw.github.com/mltframework/mlt-scripts/master/build/build-melt.sh
chmod +x build-melt.sh

echo "FFMPEG_SUPPORT_FAAC=1" >> build-melt.conf
./build-melt.sh -c build-melt.conf

cd ~/bin
ln -sf ~/melt/$(date +'%Y%m%d')/melt
cd ..

