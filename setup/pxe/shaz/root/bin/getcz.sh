#!/bin/bash -xe

# fstab:
# /var/lib/tftpboot/util/cz/expr.iso /var/lib/tftpboot/util/cz/exper iso9660 loop,defaults,ro 0 0

# http://clonezilla.org/downloads/alternative-testing/iso-zip-files.php

cd /var/lib/tftpboot/util/cz
wget -N http://downloads.sourceforge.net/project/clonezilla/clonezilla_live_alternative_testing/20111025-oneiric/clonezilla-live-20111025-oneiric.iso

# wget new iso
ln -sf clonezilla-live-20111025-oneiric.iso expr.iso
mkdir -p expr

/etc/init.d/nfs-kernel-server stop
umount /var/lib/tftpboot/util/cz/exper
mount /var/lib/tftpboot/util/cz/exper
/etc/init.d/nfs-kernel-server start

