#!/bin/bash -xe

# Files needed for PXE install ubuntu

# run this on target box

WEBROOT=/usr/share/nginx/www
SHAZ=$(hostname)

apt-get --assume-yes install  \
 dhcp3-server \
 tftpd-hpa \
 syslinux \
 nginx \
 bind9 \
 nfs-kernel-server \
 installation-guide-i386 \
 squid-deb-proxy \

# convience for checking things
ln -sf $WEBROOT


# dhcp server:
cp -rv shaz/etc/dhcp3/* /etc/dhcp/
# fix the different path 
sed -i "/dhcp3/s//dhcp/"  /etc/dhcp/dhcpd.conf
service isc-dhcp-server restart
service isc-dhcp-server stop

# 404 when the file is not found!! (duh)
# this is the stupid line that comes from the .deb
# try_files $uri $uri/ /index.html; 
# and add in autoindex - cuz it is handy.
sed -i "/^[[:space:]]*try_files \$uri \$uri\/ \/index.html;/s/.*/#cfk# &\n\t\tautoindex on;/" \
    /etc/nginx/sites-available/default
service nginx start

# put pxe boot config and binaries in place
cp -rv shaz/var/lib/tftpboot/* /var/lib/tftpboot/
cp -r /usr/lib/syslinux/ /var/lib/tftpboot/
# pxelinux.cfg/default is relitive to where it finds pxelinux.0
# (i guess)
ln -sf syslinux/pxelinux.0  /var/lib/tftpboot/

# swap shaz for whatever this box's name is.
sed -i "/shaz/s//$SHAZ/g" /var/lib/tftpboot/pxelinux.cfg/default

# get ubuntu net boot kernel/initrd
http_proxy=g2a:8000 shaz/root/bin/getu.sh oneiric
http_proxy=g2a:8000 shaz/root/bin/getu.sh precise

# setup d-i preseed files and scripts
# docs I like
# http://www.debian.org/releases/stable/i386/apbs05.html.en
cp -rv shaz/var/www/* $WEBROOT
cd $WEBROOT/ubuntu/oneiric/
cp /usr/share/doc/installation-guide-i386/example-preseed.txt.gz .
gunzip --force example-preseed.txt.gz
cd -

# setup ssh keys
# make sure the server box has keys for the user
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    ssh-keygen -f ~/.ssh/id_rsa -N ""
fi
# gen some keys for the nodes
# same keys on all nodes so that any box can ssh to any other node
cd $WEBROOT/lc/ssh
ssh-keygen -f id_rsa -N ""
chmod a+r id_rsa id_rsa.pub
echo <<EOT >>config
StrictHostKeyChecking no
EOT
cat id_rsa.pub ~/.ssh/id_rsa.pub >> authorized_keys
cd -

# squid cache of install files
# allow ppa's, repo keys
cp -rv shaz/etc/squid-deb-proxy/* /etc/squid-deb-proxy/
service squid-deb-proxy restart
# set preseeed to use proxy
# g2a is the proxy used for develment
# #commented out for developing.
# sed -i "/g2a.personnelware.com/s//$SHAZ/g" \
#    $WEBROOT/ubuntu/oneiric/preseed_user.cfg

# handy utilites
# memtest
mkdir -p /var/lib/tftpboot/util
cd /var/lib/tftpboot/util
wget -N http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
gunzip --force memtest86+-4.20.bin.gz
# clonezilla
# /var/lib/tftpboot/util/cz/getcz.sh
cd -

