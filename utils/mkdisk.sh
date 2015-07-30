#!/bin/bash -ex

lab=$1

# pumount /dev/sdc1
sudo mkfs.ext4 -L $lab -O sparse_super,extent,uninit_bg -E lazy_itable_init=1 -m 0 /dev/sdc1
sleep 5
pmount /dev/sdc1
# mkdir /media/carl/$lab/Videos
# chmod a+w /media/carl/$lab/Videos
sudo mkdir /media/sdc1/Videos
sudo chmod a+w /media/sdc1/Videos
