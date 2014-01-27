#!/bin/sh
. /scripts/A-config.sh
echo Restarting remote VGA capture device...
echo MAKE SURE VGA INPUT IS SELECTED ON THE TWINPACT
sudo killall -9 ssh
ssh avuser@$DVTWINPACT sudo /scripts/1-maincamera.sh

