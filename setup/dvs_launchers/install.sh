#!/bin/sh

USER=avuser

cp -pr Desktop/* /home/$USER/Desktop/
chown $USER:$USER /home/$USER/Desktop/*
chmod u+x /home/$USER/Desktop/*.desktop

cp -pr scripts/* /scripts/
chmod u+x /scripts/*.sh

echo "Edit /scripts/A-config.sh with room name & correct IP's"
echo "Then copy /scripts and /etc/sudoers to twinpact PC"
 
