#!/bin/bash -xe

SERVER=pc9d
DVDIR=~/Videos/veyepar/dv/$(hostname)
CLIENT=pyconde
SHOW=pyconde2011
DVDIR=~/Videos/dv/room_c
ROOM=Saal_1C

# gen and copy ssh key to server
if [ ! -f ~/.ssh/id_rsa.pub ]; then ssh-keygen; fi 
ssh-copy-id $SERVER.local:

# mount sever under ~/mnt
# sudo apt-get install sshfs
mkdir -p mnt/$SERVER
sshfs $SERVER.local: mnt/$SERVER

# swap local veyepar for server
# TODO: check for not symlink
if [ -d veyepar ]; then
  mv veyepar veyepar.local
  ln -s mnt/$SERVER/veyepar/
fi

# make local dirs
source /usr/local/bin/virtualenvwrapper.sh
set +e
workon veyepar
set -e
cd veyepar/dj/scripts/
python mkdirs.py

# swap local ogv/mp4 output dirs for ones on server
cd ~/Videos/veyepar/$CLIENT/$SHOW/
rmdir ogv mp4 
mv bling bling.local
ln -s ~/mnt/$SERVER/Videos/veyepar/$CLIENT/$SHOW/ogv
ln -s ~/mnt/$SERVER/Videos/veyepar/$CLIENT/$SHOW/mp4
ln -s ~/mnt/$SERVER/Videos/veyepar/$CLIENT/$SHOW/bling

# link local dv dir to dvsmon dv dir
# need to figure out what location slug dir 

cd dv
rmdir *
ln -s $DVDIR $ROOM

# restrict veyepart to just this room
cat <<EOT >> ~/veyepar.cfg
[global]
room=$ROOM
EOT

