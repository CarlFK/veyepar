#!/bin/bash -xe

# Files needed for PXE install ubuntu

# run this on target box

WEBROOT=/usr/share/nginx/www

sudo apt-get install  \
 dhcp3-server \
 tftpd-hpa \
 syslinux \
 nginx \
 squid-deb-proxy \
 nfs-kernel-server  

sudo cp -rv shaz/etc /
sudo cp -rv shaz/var/lib/tftpboot /var/lib/
sudo cp -rv shaz/var/www/* $WEBROOT/

ln -sf /var/lib/tftpboot/ubuntu/ $WEBROOT/
ln -sf /usr/lib/syslinux/ /var/lib/tftpboot/
ln -sf syslinux/pxelinux.0 /var/lib/tftpboot/

cd /var/lib/tftpboot/ubuntu/oneiric/
wget -N http://help.ubuntu.com/11.10/installation-guide/example-preseed.txt

mkdir -p /var/lib/tftpboot/util
cd /var/lib/tftpboot/util
wget http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
# /var/lib/tftpboot/util/cz/getcz.sh

service isc-dhcp-server restart
