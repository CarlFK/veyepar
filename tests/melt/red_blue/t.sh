#!/bin/bash -xe

melt -verbose \
 -profile dv_ntsc \
 -audio-track \
 -producer noise \
 out=30 \
 -video-track \
 $0 \
 out=30 \
 meta.attr.titles=1 \
 meta.attr.titles.markup=#timecode# \
  -attach data_show dynamic=1 \
 -consumer avformat:test.dv \
 pix_fmt=yuv411p

 mplayer test.dv
