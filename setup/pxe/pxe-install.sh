#!/bin/bash -xe

# Files needed for PXE install ubuntu

# run this on target box

WEBPROXY=g2a:8000
WEBROOT=/usr/share/nginx/www
SHAZ=$(hostname)
# WEBPROXY=$SHAZ:8000
WEBPROXY=g2a:8000

apt-get install  \
 dhcp3-server \
 tftpd-hpa \
 syslinux \
 nginx \
 nfs-kernel-server \
 installation-guide-i386 
 # squid-deb-proxy \

cp -rv srv/etc/dhcp3/* /etc/dhcp/
cp -rv srv/var/lib/tftpboot/* /var/lib/tftpboot/
cp -rv srv/var/www/* $WEBROOT

# fix the different path
sed -i "/dhcp3/s//dhcp/"  /etc/dhcp/dhcpd.conf

# put pxe boot binaries in place
cp -r /usr/lib/syslinux/ /var/lib/tftpboot/
# pxelinux.cfg/default is relitive to where it fins pxelinux.0
# (i guess)
ln -s syslinux/pxelinux.0  /var/lib/tftpboot/

# swap shaz for whatever this box's name is.
sed -i "/shaz/s//$SHAZ/g" /var/lib/tftpboot/pxelinux.cfg/default

# get ubuntu net boot kernel/initrd
http_proxy=$WEBPROXY srv/root/bin/getu.sh oneiric

cd $WEBROOT/ubuntu/oneiric/
cp /usr/share/doc/installation-guide-i386/example-preseed.txt.gz .
gunzip example-preseed.txt.gz

mkdir -p /var/lib/tftpboot/util
cd /var/lib/tftpboot/util
wget -N http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
# /var/lib/tftpboot/util/cz/getcz.sh

service isc-dhcp-server restart
service isc-dhcp-server stop

service nginx start
