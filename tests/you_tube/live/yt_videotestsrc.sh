#!/bin/bash -ex
#   
# stormer: CarlFK: you don't need flashVer, videoKeyFrameRequency anymore
# stormer: this is all legacy in snowmix


# sudo apt-get install vim less tmux
# sudo apt-get install gstreamer1.0-plugins-ugly  # errored.
# sudo aptitude -t wheezy-backports install gstreamer1.0-plugins-ugly
# sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-bad
# sudo apt-get install gstreamer0.10-plugins-bad-multiverse

source auth.sh

gst-launch-1.0 \
        videotestsrc pattern=18 is-live=1 \
        ! video/x-raw, framerate=30/1, width=426, height=240 \
        ! timeoverlay \
        ! x264enc bitrate=2000 key-int-max=60 bframes=0 byte-stream=false aud=true tune=zerolatency \
        ! h264parse \
        ! "video/x-h264,profile=main" \
        ! queue \
        ! mux. audiotestsrc is-live=true \
        ! "audio/x-raw, format=(string)S16LE, endianness=(int)1234, signed=(boolean)true, width=(int)16, depth=(int)16, rate=(int)44100, channels=(int)2" \
        ! voaacenc bitrate=128000 \
        ! flvmux streamable=true name=mux \
        ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/x/$AUTH app=live2"

exit

# https://bugzilla.gnome.org/show_bug.cgi?id=731352#c6
gst-launch-1.0 \
    videotestsrc is-live=1 \
        ! "video/x-raw, width=1280, height=720, framerate=30/1" \
        ! timeoverlay \
        ! x264enc bitrate=2000 ! "video/x-h264,profile=main" \ 
      ! queue ! mux. \
    audiotestsrc is-live=1 wave=12 ! faac ! queue ! mux. \
    flvmux streamable=1 name=mux  \ 
      ! rtmpsink location="rtmp://a.rtmp.youtube.com/live2/x/$AUTH app=live2"
