#! /bin/sh -x

SHAZ=192.168.2.1

# install the scp command:
anna-install openssh-client-udeb

# create a place for custom stuff
mkdir -p /tmp/misc
# copy this script incase we need to ship this dir of in a bug report
# the script to copy files off for a bug report
cp $0 /tmp/misc
cd /tmp/misc
wget http://$SHAZ/cpl.sh
chmod u+x cpl.sh 

# scrpt to install sshd and keys
wget http://$SHAZ/isshd.sh
chmod u+x isshd.sh
./isshd.sh

