#!/bin/bash -xe

# Files needed for PXE install ubuntu

# run this on target box

WEBPROXY=g2a:8000
WEBROOT=/usr/share/nginx/www
SHAZ=$(hostname)
# WEBPROXY=$SHAZ:8000
WEBPROXY=g2a:8000

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

# 404 when the file is not found!! (duh)
# this is the stupid line that comes from the .deb
# try_files $uri $uri/ /index.html; 
# and add in autoindex - cuz it is handy.
sed -i "/^[[:space:]]*try_files \$uri \$uri\/ \/index.html;/s/.*/#cfk# &\n\t\tautoindex on;/" /etc/nginx/sites-available/default

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
http_proxy=g2a:8000 shaz/root/bin/getu.sh precise

# setup d-i preseed files
# docs I like
# http://www.debian.org/releases/stable/i386/apbs05.html.en
cd $WEBROOT/ubuntu/oneiric/
cp /usr/share/doc/installation-guide-i386/example-preseed.txt.gz .
gunzip --force example-preseed.txt.gz
cd -


mkdir -p /var/lib/tftpboot/util
cd /var/lib/tftpboot/util
wget -N http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
# /var/lib/tftpboot/util/cz/getcz.sh
cd -

service isc-dhcp-server restart
service isc-dhcp-server stop

service squid-deb-proxy restart
service nginx start
