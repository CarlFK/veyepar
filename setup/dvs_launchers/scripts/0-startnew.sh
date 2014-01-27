#!/bin/sh

. /scripts/A-config.sh

echo Killing all current sources...
killall dvswitch
killall -9 dvswitch
killall dvgrab
killall -9 dvgrab

dvswitch &
sleep 4
/scripts/2-audiomixer.sh &
sleep 2
/scripts/1-maincamera.sh &
/scripts/3-vgacapture.sh &
/scripts/4-nfssink.sh &
dvsink-files $LOCALDV/$ROOMNAME/%Y-%m-%d/%H_%M_%S.dv
 
# ogvfwd streaming
# xterm /scripts/5-streaming.sh &

