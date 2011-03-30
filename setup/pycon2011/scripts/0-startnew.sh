#!/bin/sh

. /scripts/A-config.sh

mkdir $LOCALDV 2> /dev/null
mkdir $LOCALDV/$ROOMNAME 2> /dev/null
mkdir $LOCALDV/$ROOMNAME/$DATE 2> /dev/null

echo Killing all current sources...
killall dvswitch
killall -9 dvswitch
killall dvgrab
killall -9 dvgrab
dvswitch -h $DVHOST -p $DVPORT &
sleep 4
/scripts/2-audiomixer.sh &
sleep 2
/scripts/1-maincamera.sh &
/scripts/3-vgacapture.sh &

dvsink-files $LOCALDV/$ROOMNAME/$DATE/%T.dv 
 
