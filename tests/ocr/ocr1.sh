#!/bin/bash -x

echo INVALID>source.txt

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

gocr -s 40 -C A-Z 00000001.ppm
