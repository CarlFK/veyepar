#!/bin/sh
. /scripts/A-config.sh

echo Restarting streaming...
killall -9 ffmpeg2theora
killall -9 oggfwd
while (true); do nice -n 5 dvsink-command -h $DVHOST -p $DVPORT -- ffmpeg2theora - -f dv -x 352 -y 288 --speedlevel 2 -v 4 -a 0 -c 1 -H 48000 -o - | oggfwd 192.168.128.10 8000 sastUcUg4 /lca2011-${ROOMNAME}; echo Streaming crashed, sleeping 10 seconds...; sleep 10; done


