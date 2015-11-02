#!/bin/bash -x

sudo apt-add-repository multiverse
sudo apt-get --assume-yes install libphonon-dev phonon-backend-gstreamer
sudo apt-get --assume-yes install git automake autoconf libtool intltool g++ yasm swig libmp3lame-dev libgavl-dev libsamplerate-dev libxml2-dev ladspa-sdk libjack-dev libsox-dev libsdl-dev libgtk2.0-dev liboil-dev libsoup2.4-dev libqt4-dev libexif-dev libtheora-dev libvdpau-dev libvorbis-dev python-dev kdelibs5-dev cmake libvpx-dev libfaac-dev libeigen3-dev libglew-dev
sudo apt-get --assume-yes install yasm cmake xutils-dev libegl1-mesa-dev libfftw3-dev libsdl1.2-dev libfaac-dev libvorbis-dev libmp3lame-dev libtheora-dev swig libgtk2.0-dev libjack-dev libsamplerate0-dev libsox-dev libjack0

mkdir -p melt
cd melt
wget -N https://raw.github.com/mltframework/mlt-scripts/master/build/build-melt.sh
chmod +x build-melt.sh

echo "FFMPEG_SUPPORT_FAAC=1" >> build-melt.conf
./build-melt.sh -c build-melt.conf

mkdir ~/bin
cd ~/bin
ln -sf ~/melt/$(date +'%Y%m%d')/melt
cd ..

