sudo apt-get install vim less tmux
sudo apt-get install gstreamer1.0-plugins-ugly  # errored.
sudo aptitude -t wheezy-backports install gstreamer1.0-plugins-ugly
sudo apt-get install gstreamer1.0-tools gstreamer1.0-plugins-bad

gst-launch-1.0 -v --gst-debug=flvmux:0,rtmpsink:0 videotestsrc pattern=18 is-live=true ! video/x-raw, framerate=30/1, width=426, height=240 ! queue ! videoconvert ! x264enc bitrate=400 key-int-max=60 bframes=0 byte-stream=false aud=true tune=zerolatency ! h264parse ! "video/x-h264,level=(string)4.1,profile=main" ! queue ! mux. audiotestsrc is-live=true ! "audio/x-raw, format=(string)S16LE, endianness=(int)1234, signed=(boolean)true, width=(int)16, depth=(int)16, rate=(int)44100, channels=(int)2" ! queue ! voaacenc bitrate=128000 ! aacparse ! audio/mpeg,mpegversion=4,stream-format=raw ! queue ! flvmux streamable=true name=mux ! queue ! rtmpsink "location=rtmp://a.rtmp.youtube.com/live2/x/apssids-2681.wsb6-pym5-fqeu-fs59?videoKeyframeFrequency=1&totalDatarate=4128" app=live2 flashVer="FME/3.0%20(compatible;%20FMSc%201.0)" swfUrl=rtmp://a.rtmp.youtube.com/live2
