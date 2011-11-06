#!/bin/bash -xe

# Files needed for PXE install ubuntu

# run this on target box

WEBPROXY=g2a:8000
WEBROOT=/usr/share/nginx/www
SHAZ=$(hostname)
WEBPROXY=$SHAZ:8000
# WEBPROXY=g2a:8000

apt-get --assume-yes install  \
 dhcp3-server \
 tftpd-hpa \
 syslinux \
 nginx \
 nfs-kernel-server \
 installation-guide-i386 \
 squid-deb-proxy \

# convience for checking things
ln -sf $WEBROOT

cp -rv shaz/etc/dhcp3/* /etc/dhcp/
cp -rv shaz/var/lib/tftpboot/* /var/lib/tftpboot/
cp -rv shaz/var/www/* $WEBROOT

# allow ppa's, repo keys
cp -rv shaz/etc/squid-deb-proxy/* /etc/squid-deb-proxy/

# fix the different path 
sed -i "/dhcp3/s//dhcp/"  /etc/dhcp/dhcpd.conf

# gen some keys for the nodes
# same keys on all nodes so that any box can ssh to any other node
mkdir -p shaz/var/www/lc/ssh
cd shaz/var/www/lc/ssh
ssh-keygen -f id_rsa -N ""
cp id_rsa.pub authorized_keys
echo <<EOT >>config
StrictHostKeyChecking no
EOT

# put pxe boot binaries in place
cp -r /usr/lib/syslinux/ /var/lib/tftpboot/
# pxelinux.cfg/default is relitive to where it fins pxelinux.0
# (i guess)
ln -sf syslinux/pxelinux.0  /var/lib/tftpboot/

# swap shaz for whatever this box's name is.
sed -i "/shaz/s//$SHAZ/g" /var/lib/tftpboot/pxelinux.cfg/default
sed -i "/g2a.personnelware.com:8000/s//$WEBPROXY/g" $WEBROOT/ubuntu/oneiric/preseed_user.cfg

# get ubuntu net boot kernel/initrd
# remove proxy for production
http_proxy=g2a:8000 shaz/root/bin/getu.sh oneiric

cd $WEBROOT/ubuntu/oneiric/
cp /usr/share/doc/installation-guide-i386/example-preseed.txt.gz .
gunzip example-preseed.txt.gz

mkdir -p /var/lib/tftpboot/util
cd /var/lib/tftpboot/util
wget -N http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
# /var/lib/tftpboot/util/cz/getcz.sh

service isc-dhcp-server restart
service isc-dhcp-server stop

service squid-deb-proxy restart
service nginx start
