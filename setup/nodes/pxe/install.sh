#!/bin/bash -xe

# installs packages, configs and scripts for PXE install ubuntu

# run this to setup pxe server

# change scripts to reference this box
SHAZ=$(hostname)
# change scripts to use this user
NUSER=$SUDO_USER
NUSER=videoteam

# default webroot for nginx
# WEBROOT=/usr/share/nginx/www
WEBROOT=/usr/share/nginx/html

apt-get --force-yes --assume-yes install  \
    python-software-properties \

#    debconf

# this has the squid-deb-proxy config that allows PPAs
# apt-add-repository --yes ppa:carlfk
# apt-get update

# debconf-set-selections -v <<< \
#    "squid-deb-proxy squid-deb-proxy/ppa-enable boolean true" 

apt-get --force-yes --assume-yes install  \
 dhcp3-server \
 bind9 \
 tftpd-hpa \
 syslinux \
 nginx \
 nfs-kernel-server \
 installation-guide-i386 \
 squid-deb-proxy \

# dhcp server:
cp -rv shaz/etc/dhcp* /etc/

# needed for ddns
# give dhcpd process access to this file
# include "/etc/bind/rndc.key";
adduser dhcpd bind

# tell apparor to allow dhcpd process to read the dns keyfile
cat <<EOT >>/etc/apparmor.d/local/usr.sbin.dhcpd
/etc/bind/rndc.key r,
EOT
service apparmor restart

# setup dns
cp shaz/etc/bind/named.conf.local /etc/bind/
cp shaz/var/cache/bind/db.private  /var/cache/bind/
cp shaz/var/cache/bind/rev.z.y.x.in-addr.arpa /var/cache/bind/
sed -i "/shaz/s//$SHAZ/g" \
    /var/cache/bind/db.private \
    /var/cache/bind/rev.z.y.x.in-addr.arpa
touch /var/cache/bind/managed-keys.bind
chown bind:bind /var/cache/bind/*

# lets not start the dhcp server just yet.
# having 2 dhcp servers on 1 lan is dumb.
# service isc-dhcp-server restart

service bind9 start

## ddns setup done.

# setup pxe and ubuntu install scripts

# put pxe boot config and binaries in place
cp -rv shaz/var/lib/tftpboot/* /var/lib/tftpboot/
cp -r /usr/lib/syslinux/ /var/lib/tftpboot/
# pxelinux.cfg/default is relitive to where it finds pxelinux.0
# (i guess)
ln -sf syslinux/pxelinux.0  /var/lib/tftpboot/

# swap shaz for whatever this box's name is.
sed -i "/shaz/s//$SHAZ/g" /var/lib/tftpboot/pxelinux.cfg/default

if [[ "$(hostname)" =~ trist|pc8|chris|baz ]]; then
   export http_proxy=http://g2a:8000
fi
## get ubuntu net boot kernel/initrd
# shaz/root/bin/getu.sh maverick amd64
# shaz/root/bin/getu.sh natty amd64
shaz/root/bin/getu.sh oneiric amd64
shaz/root/bin/getu.sh oneiric i386
shaz/root/bin/getu.sh precise amd64
shaz/root/bin/getu.sh precise i386

# setup d-i preseed files and scripts
# docs I like
# http://www.debian.org/releases/stable/i386/apbs05.html.en
cp -rv shaz/var/www/* $WEBROOT
cd $WEBROOT/d-i/oneiric/
cp /usr/share/doc/installation-guide-i386/example-preseed.txt.gz .
gunzip --force example-preseed.txt.gz
cd -

# setup ssh keys
# make sure the server box has keys for the user
if [ ! -f ~/.ssh/id_rsa.pub ]; then
    mkdir -p ~/.ssh
    ssh-keygen -f ~/.ssh/id_rsa -N ""
fi
# gen some keys for the nodes
# same keys on all nodes so that any box can ssh to any other node
# ec/ssh is to ssh into the installer (for debugging the install)
cd $WEBROOT/ec/ssh
cat ~/.ssh/id_rsa.pub >> authorized_keys
cd -
cd $WEBROOT/lc/ssh
ssh-keygen -f id_rsa -N ""
chmod a+r id_rsa id_rsa.pub
cat <<EOT >>config
StrictHostKeyChecking no
EOT
cat id_rsa.pub ~/.ssh/id_rsa.pub >> authorized_keys
cd -

# fix nginx config:
# not needed for production, but default is anoying to debug.
# current behavior: if file not found, fall back to index.html 
# fix it to make it 404 when the file is not found!! 
# this is the stupid line that comes from the .deb
# try_files $uri $uri/ /index.html; 
# and add in autoindex - cuz it is handy.
sed -i "/^[[:space:]]*try_files \$uri \$uri\/ \/index.html;/s/.*/#cfk# &\n\t\tautoindex on;/" \
    /etc/nginx/sites-available/default

service nginx start

# nodes will have the same user as the server box
sed -i "/@user@/s//$NUSER/g" \
    $WEBROOT/d-i/oneiric/preseed_local.cfg

# squid cache the install files
# allow ppa's, repo keys
# note: http://www.squid-cache.org/Doc/config/offline_mode/
#

if [[ "$(hostname)" =~ trist|pc8|chris|baz ]]; then
 # local cache used to speed up testing this script
 # not needed for production
 cat <<EOT >> /etc/squid-deb-proxy/squid-deb-proxy.conf
cache_peer g2a parent 8000 8002 
never_direct allow all
EOT
printf "www.memtest.org\n" \
    >> /etc/squid-deb-proxy/mirror-dstdomain.acl.d/90-debug
fi

service squid-deb-proxy restart

# set preseeed to use proxy
# g2a is the proxy used for development
sed -i "/g2a.personnelware.com/s//$SHAZ/g" \
    $WEBROOT/d-i/oneiric/preseed_local.cfg

# handy utilites
# memtest
mkdir -p /var/lib/tftpboot/util
cd /var/lib/tftpboot/util
wget -N http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
gunzip --force memtest86+-4.20.bin.gz
wget http://www.memtest.org/download/5.01/memtest86+-5.01.floppy.zip
# clonezilla
# 400mb iso.... come back if you raelly need it.
# /var/lib/tftpboot/util/cz/getcz.sh
cd -

echo setup static IP in range of 192.168.0.1-9
echo sudo service isc-dhcp-server start

