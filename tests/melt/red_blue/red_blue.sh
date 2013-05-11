#!/bin/bash -xe

melt -verbose \
 -profile dv_ntsc \
 red_blue.mlt \
 meta.attr.titles=1 \
 meta.attr.titles.markup=#timecode# \
  -attach data_show dynamic=1 \
 -consumer avformat:red_blue.dv \
 pix_fmt=yuv411p

 mplayer red_blue.dv
