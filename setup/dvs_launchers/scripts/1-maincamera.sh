#!/bin/sh

. /scripts/A-config.sh

echo Restarting local firewire capture...
sudo killall dvsource-firewire
sudo killall -9 dvsource-firewire
sudo killall dvgrab
sudo killall -9 dvgrab
sleep 2

dvsource-firewire 
