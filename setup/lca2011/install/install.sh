#!/bin/sh

sudo chown avuser ~avuser/.ssh/id_rsa

cp -pr Desktop/* /home/avuser/Desktop/
chown avuser:avuser /home/avuser/Desktop/*
chmod +x /home/avuser/Desktop/*.desktop

chown avuser:avuser /home/avuser/Desktop/dv
mkdir /home/avuser/Desktop/dv/nd
chown root:root /home/avuser/Desktop/dv/nd
chmod a-w /home/avuser/Desktop/dv/nd

cp -pr scripts/* /scripts/
chmod +x /scripts/*.sh

echo "192.168.128.1:/mnt/lcadata      /home/avuser/Desktop/dv/nd      nfs     intr,hard,rsize=8192,wsize=8192 0       0" >> /etc/fstab
vi /etc/fstab

echo "%admin ALL=NOPASSWD: ALL" >> /etc/sudoers
vi /etc/sudoers

echo "NOW DO THE FOLLOWING:"
echo "System -> Preferences - Mouse -> touchpad.  disable enable clicks with touchpad - AND scrolling"
echo "Disable wifi"
echo "Edit /scripts/A-config.sh with room name & correct IP's"
echo "Then copy /scripts and /etc/sudoers to twinpact PC"
 
