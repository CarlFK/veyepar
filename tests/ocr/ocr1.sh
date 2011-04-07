#!/bin/bash -x

# clean up previous runs
rm test.mp4 00000001.ppm

echo ABCDEFG>source.txt

melt -verbose \
 -profile dv_ntsc \
 -audio-track \
 -producer noise \
 out=0 \
 -video-track \
 source.txt \
 out=0 \
 -consumer avformat:test.mp4

mplayer -vo pnm test.mp4

# display 00000001.ppm

if [[ "$(gocr -s 40 -C A-Z 00000001.ppm)" == "ABCDEFG" ]] ; then
   echo pass
   exit 0
else
   echo fail 
   exit 1
fi
