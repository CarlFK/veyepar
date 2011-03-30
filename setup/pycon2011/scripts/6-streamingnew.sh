#!/bin/sh
. /scripts/A-config.sh

echo Restarting streaming...
killall -9 ffmpeg2theora
killall -9 oggfwd
# 576 432

while (true); do nice -n 5 dvsink-command -h $DVHOST -p $DVPORT -- ffmpeg2theora - --aspect 4:3 --pixel-aspect 16:15 --no-skeleton -f dv -F 25:2 --speedlevel 2 -v 6 -a 0 -c 1 -H 48000 --title "{$CONFNAME} {$ROOMNAME}" -o - | oggfwd $STREAMIP $STREAMPORT $STREAMPASS /${CONFNAME}-${ROOMNAME}; echo Streaming crashed, sleeping 10 seconds...; sleep 10; done


