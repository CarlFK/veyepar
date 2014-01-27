#!/bin/sh

USER=avuser

# original line, pretty sure it errors:
# sudo chown avuser ~avuser/.ssh/id_rsa

cp -pr Desktop/* /home/$USER/Desktop/
chown avuser:avuser /home/$USER/Desktop/*
chmod +x /home/$USER/Desktop/*.desktop

chown $USER:$USER /home/$USER/Desktop/dv
mkdir /home/avuser/Desktop/dv/nd
chown root:root /home/avuser/Desktop/dv/nd
chmod a-w /home/avuser/Desktop/dv/nd

cp -pr scripts/* /scripts/
chmod +x /scripts/*.sh

echo "192.168.128.1:/mnt/lcadata      /home/avuser/Desktop/dv/nd      nfs     intr,hard,rsize=8192,wsize=8192 0       0" >> /etc/fstab
vi /etc/fstab

echo "%admin ALL=NOPASSWD: ALL" >> /etc/sudoers
vi /etc/sudoers

echo "Edit /scripts/A-config.sh with room name & correct IP's"
echo "Then copy /scripts and /etc/sudoers to twinpact PC"
 
