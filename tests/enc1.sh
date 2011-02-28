#!/bin/bash -x


echo test1>source.txt

melt -verbose \
 -profile dv_ntsc \
 -audio-track \
 -producer noise \
 out=30000 \
 -video-track \
 source.txt \
 out=30000 \
 meta.attr.titles=1 \
 meta.attr.titles.markup=#timecode# \
 -attach data_show dynamic=1 \
 -consumer avformat:test.flv progressive=1 acodec=libfaac ab=96k ar=44100 vcodec=libx264 b=240k vpre=/usr/share/ffmpeg/libx264-hq.ffpreset

