#!/bin/bash -x

sudo apt-get install automake autoconf libtool intltool g++ yasm swig libmp3lame-dev libgavl-dev libsamplerate-dev libxml2-dev ladspa-sdk libjack-dev libsox-dev libsdl-dev libgtk2.0-dev libqt4-dev libexif-dev libtheora-dev libvdpau-dev libvorbis-dev python-dev libvpx-dev liboil0.3-dev

mkdir -p melted
cd melted
wget -N http://www.mltframework.org/twiki/pub/MLT/BuildScripts/build-melted.sh
chmod +x build-melted.sh

./build-melted.sh

cd ~/bin
ln -sf ~/melted/$(date +'%Y%m%d')/bin/melt
cd ..

exit
source .virtualenvs/veyepar/bin/activate
cd veyepar/dj/scripts
./rt.sh
