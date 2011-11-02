# Files needed for PXE install ubuntu

# sudo apt-get install 
 dhcp3-server 
 tftpd-hpa
 syslinux
 nginx
 squid-deb-proxy 
 nfs-kernel-server 

# ln -s /var/lib/tftpboot/ubuntu/ /var/www/
# ln -s /usr/lib/syslinux/ /var/lib/tftpboot/

# # ln -s /usr/lib/syslinux/pxelinux.0 /var/lib/tftpboot/

# http://www.memtest.org/download/4.20/memtest86+-4.20.bin.gz
# http://help.ubuntu.com/11.10/installation-guide/example-preseed.txt

/etc/dhcp3/dhcpd.conf
/etc/dhcp3/dhcpd.conf.macs

# /var/lib/tftpboot/pxelinux.0
# /var/lib/tftpboot/syslinux/chain.c32
# /var/lib/tftpboot/memdisk

/var/lib/tftpboot/pxelinux.cfg/default

/var/lib/tftpboot/util/cz/getcz.sh

/var/lib/tftpboot/ubuntu/oneiric/*
/var/lib/tftpboot/ubuntu/oneiric/preseed.cfg
/var/lib/tftpboot/ubuntu/oneiric/preseed_carl.cfg
/var/lib/tftpboot/ubuntu/oneiric/preseed_user.cfg
/var/lib/tftpboot/ubuntu/oneiric/getu.sh

/var/lib/tftpboot/ubuntu/oneiric/amd64/initrd.gz  
/var/lib/tftpboot/ubuntu/oneiric/amd64/linux
/var/lib/tftpboot/ubuntu/oneiric/i386/initrd.gz  
/var/lib/tftpboot/ubuntu/oneiric/i386/linux

/var/www/ec/*
/var/www/ec/cpl.sh
/var/www/ec/early_command.sh
/var/www/ec/isshd.sh

/var/www/lc/*
/var/www/lc/nm
/var/www/lc/nm/dhcpipv4.conf
/var/www/lc/nm/10.0.0.1.conf
/var/www/lc/nm/auto-magic.conf
/var/www/lc/authorized_keys
/var/www/lc/async-test
/var/www/lc/mkmlt.sh
/var/www/lc/netcons.sh
/var/www/lc/fw-beep.rules
/var/www/lc/hook.sh
/var/www/lc/mp.conf
/var/www/lc/build-melted.sh
/var/www/lc/late.sh
/var/www/lc/local.dconf

