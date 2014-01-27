#!/bin/sh

. /scripts/A-config.sh

echo Restarting remote VGA capture device...
echo MAKE SURE VGA INPUT IS SELECTED ON THE TWINPACT
# ssh $DVTWINPACT killall -9 ssh

ssh $DVTWINPACT /scripts/1-maincamera.sh

