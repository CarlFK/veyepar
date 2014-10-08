#!/bin/bash -ex
# Read from DVswitch, encode to a 2mbs stream and send to youtube-live.

source ~/.dvswitchrc
source auth.sh

gst-launch-0.10 -v \
    dvswitchsrc hostname=$MIXER_HOST port=$MIXER_PORT \
    ! dvdemux name=demux \
    ! queue \
    ! dvdec \
    ! ffmpegcolorspace \
    ! x264enc \
          bitrate=2000 key-int-max=60 bframes=0 \
          byte-stream=false aud=true tune=zerolatency \
	! h264parse \
	! "video/x-h264,profile=main" \
	! flvmux streamable=true name=mux \
    ! rtmpsink \
        location="$PSERV/x/$AUTH app=live2"  \
        demux. \
    ! queue \
    ! audioconvert \
    ! voaacenc bitrate=128000 \
    ! mux.

