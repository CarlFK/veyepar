#!/bin/bash -ex

lab=$1
dev=sdd1
mp=/media/carl/$lab

# pumount /dev/$dev
sudo mkfs.ext4 -L $lab -O sparse_super,extent,uninit_bg -E lazy_itable_init=1 -m 0 /dev/$dev
# sudo mkfs.ntfs /dev/sdc1 --label nodevids1415 --fast --no-indexing

sleep 5
pmount /dev/$dev
exit

mp=/media/$dev

# mkdir /media/carl/$lab/Videos
# chmod a+w /media/carl/$lab/Videos
# sudo mkdir /media/$dev/Videos
# sudo chmod a+w /media/$dev/Videos
sudo mkdir $mp/Videos
sudo chmod a+w $mp/Videos
mkdir $mp/Videos/veyepar
