#mkraid.sh
# -x=display commands, -e=exit on error
set -xe

# apt-get install mdadm

# mdadm --remove /dev/md0 --force --raid-devices=8 \
# 	/dev/sda1 /dev/sdb1 /dev/sdc1 /dev/sdd1 \
#	/dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 

/etc/init.d/mdadm stop
/etc/init.d/udev stop

mdadm --stop --scan
for i in a b c d e f g h; do
  parted /dev/sd$i --script -- mktable gpt
  parted /dev/sd$i --script -- mkpart primary ext4 0% 100%
  parted /dev/sd$i --script -- print
  mdadm --stop --scan
  sfdisk -R /dev/sd$i
done
mdadm --stop --scan

# Set up md device
mdadm --create /dev/md0 --level=raid6 --bitmap=internal --raid-devices=8 --assume-clean \
	/dev/sda1 /dev/sdb1 /dev/sdc1 /dev/sdd1 \
	/dev/sde1 /dev/sdf1 /dev/sdg1 /dev/sdh1 

/etc/init.d/mdadm start
/etc/init.d/udev start
# above line may be erroring, which aborts the script? 

mkfs.ext4 /dev/md0 
e2label /dev/md0 space

mdadm --detail --scan >> /etc/mdadm/mdadm.conf

update-initramfs -u

# show us what we got 
# (well, as much as I know how to show - some sort of grub setup would be nice.)

