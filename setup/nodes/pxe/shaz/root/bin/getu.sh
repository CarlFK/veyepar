#!/bin/bash -xe
# get ubuntu installers

DIST=$1
ARCH=$2

DIR=/var/lib/tftpboot/ubuntu/$DIST/$ARCH
mkdir -p $DIR
cd $DIR
BASE=http://archive.ubuntu.com/ubuntu/dists/$DIST/main/installer-$ARCH/current/images/netboot/ubuntu-installer/$ARCH
wget -N $BASE/linux
wget -N $BASE/initrd.gz

# check for updates:
BASE=http://archive.ubuntu.com/ubuntu/dists/oneiric-updates/main/installer-i386/current/images/netboot/

cd ..

# notes:
#  http://cdimage.ubuntu.com/ubuntu-gnome/releases/14.04/beta-1/   
#  http://cdimage.ubuntu.com/daily-live/current/

