#!/bin/sh
. /scripts/A-config.sh
echo Restarting USB mixer device...
sudo killall dvsource-alsa
sudo killall -9 dvsource-alsa
dvsource-alsa hw:1 -s $TVSTD -h $DVHOST -p $DVPORT

