#!/bin/bash -xe
# setup_node.sh
# sets up a laptop to run dvswitch and be a veyepar encoding node

set -ex

# install dvswitch scrips and stuff

# Ubuntu adds ~/bin to PATH if it exists, so make it and put scripts there
if [[ ! -d ~/bin ]]; then
  mkdir ~/bin
fi
cp -v stuff/scripts/* ~/bin
chmod u+x ~/bin/*
cp -v stuff/Desktop/* ~/Desktop/
chmod +x ~/Desktop/*

# install dvs-mon so carl can use it to debug cranky systems
if [[ ! -d ~/dvsmon ]]; then
  cp -a dvsmon ~/
  chmod u+x ~/dvsmon/dvs-mon.py
fi

sudo apt-add-repository ppa:carlfk/ppa
sudo apt-get update
sudo apt-get dist-upgrade

# sudo apt-get install squid-deb-proxy-client
sudo apt-get install dvswitch dvsource dvsink gamix audacity ffmpeg mplayer vlc python-wxgtk2.8 openssh-server

# ssh-keygen

# Sudoers no password
# sudo cp stuff/sudoers /etc/sudoers
# sudo chown root:root /etc/sudoers
# sudo chmod 440 /etc/sudoers

# debian locks down firewire, so add it to the video group and add user to video group
# sudo cp stuff/udev/91-permissions.rules /etc/udev/rules.d/
sudo adduser $USER video
sudo adduser $USER admin

# set boxes hostname to room name + _slave if remote box.
# ? promtps for it
sudo python stuff/upbox.py --hostname "?"

# create .dvswitchrc if it doesn't exist
# note, 0.0.0.0 is for the master box, slave needs to be set to IP of master
if [[ ! -f .dvswitchrc ]]; then 
echo \# MIXER_HOST=10.0.0.111>~/.dvswitchrc
echo MIXER_HOST=0.0.0.0>>~/.dvswitchrc
echo MIXER_PORT=2000>>~/.dvswitchrc
fi
vi ~/.dvswitchrc

echo If this is a master box, copy ssh keys to slave 
echo ssh-copy-id 10.0.0.111
