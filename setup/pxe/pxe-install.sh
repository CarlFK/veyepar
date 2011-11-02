# Files needed for PXE install ubuntu

# run this on target box

sudo apt-get install  \
 dhcp3-server \
 tftpd-hpa \
 syslinux \
 nginx \
 squid-deb-proxy \
 nfs-kernel-server \ 

sudo rsync -rv carl@dc10:src/veyepar/setup/pxe/shaz /

ln -s /var/lib/tftpboot/ubuntu/ /var/www/
ln -s /usr/lib/syslinux/ /var/lib/tftpboot/
ln -s syslinux/pxelinux.0 /var/lib/tftpboot/

cd /var/lib/tftpboot/ubuntu/oneiric/
wget -N http://help.ubuntu.com/11.10/installation-guide/example-preseed.txt

cd /var/lib/tftpboot/util
wget http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
# /var/lib/tftpboot/util/cz/getcz.sh

