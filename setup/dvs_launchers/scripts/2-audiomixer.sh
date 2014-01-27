#!/bin/sh

. /scripts/A-config.sh

echo Restarting USB mixer device...
killall dvsource-alsa
killall -9 dvsource-alsa

dvsource-alsa hw:1

