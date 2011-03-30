#!/bin/sh
. /scripts/A-config.sh
echo Restarting local firewire capture...
sudo killall dvsource-firewire
sudo killall -9 dvsource-firewire
sudo killall dvgrab
sudo killall -9 dvgrab
sleep 2
sudo dvsource-firewire -c 1 -h $DVHOST -p $DVPORT &
sudo dvsource-firewire -h $DVHOST -p $DVPORT
