#!/bin/bash -xe
# get ubuntu installers

DIST=$1

ARCH=amd64

DIR=/var/lib/tftpboot/ubuntu/$DIST/$ARCH
mkdir -p $DIR
cd $DIR
BASE=http://archive.ubuntu.com/ubuntu/dists/$DIST/main/installer-$ARCH/current/images/netboot/ubuntu-installer/$ARCH
wget -N $BASE/linux
wget -N $BASE/initrd.gz
cd ..

ARCH=i386

DIR=/var/lib/tftpboot/ubuntu/$DIST/$ARCH
mkdir -p $DIR
cd $DIR
BASE=http://archive.ubuntu.com/ubuntu/dists/$DIST/main/installer-$ARCH/current/images/netboot/ubuntu-installer/$ARCH
wget -N $BASE/linux
wget -N $BASE/initrd.gz
cd ..

exit

amd64
BASE=http://archive.ubuntu.com/ubuntu/dists/$DIST/main/installer-amd64/current/images/netboot/ubuntu-installer/amd64
wget -N $BASE/linux
wget -N $BASE/initrd.gz
cd ..

