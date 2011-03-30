#!/bin/sh
mkdir /scripts
cp -pr * /scripts/
cp -pr Desktop/* ~/Desktop/
chmod a+rx ~/Desktop/*.desktop
echo "%admin ALL=NOPASSWD: ALL" >> /etc/sudoers

echo edit sudoers, comment out second last line - non nopasswd line
echo edit fstab, commen tout natty line 

