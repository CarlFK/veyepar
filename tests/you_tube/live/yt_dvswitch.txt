#!/bin/bash -ex
# Read from DVswitch, encode to a 2mbs stream and send to youtube-live.

"""
1500 Kbps 720p is too high.
500 (480p) is good

Protocol:   RTMP Flash Streaming
Video codec:    H.264, Main 4.1
Frame rate:     up to 60 fps
Keyframe frequency:     2 seconds
Audio codec:    AAC-LC (or MP3)
Audio sample rate:  44.1 KHz
Audio bitrate:  128 Kbps stereo
 
Keyframe Frequency must be less than or equal to 2 seconds to ensure optimal transcoding on the new platform.
Recommended advanced settings
Pixel aspect ratio:     Square
Frame types:    Progressive Scan, 2 B-Frames, 1 Reference Frame
Entropy coding:     CABAC

"""

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

