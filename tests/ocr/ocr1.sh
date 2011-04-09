#!/bin/bash -x

# create file to encode
echo ABCDEFG>source.txt

# encode to 1 frame movie
melt -verbose \
 -profile dv_ntsc \
 -audio-track \
 -producer noise \
 out=0 \
 -video-track \
 source.txt \
 out=0 \
 -consumer avformat:test.mp4

# extract the frame 
mplayer -vo pnm test.mp4


# display 00000001.ppm

# see if gocr can read the letters:
if [[ "$(gocr 00000001.ppm)" == "ABCDEFG" ]] ; then
   echo pass
   # clean up
   rm source.txt test.mp4 00000001.ppm
   exit 0
else
   echo fail 
   exit 1
fi
