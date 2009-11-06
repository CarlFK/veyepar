#!/bin/bash
# melt command by bedlore

# params: show_dir file_root
echo show_dir: $1
echo file_root: $2

IN=$1/tmp/$2.mlt
OUT=$1/mp4/$2.mp4

melt -verbose -profile square_pal_wide $IN -consumer avformat:$OUT acodec=libmp3lame ab=128k ar=44100 vcodec=mpeg4 threads=8 minrate=0 b=2000k fastfirstpass=1 aspect=1.7777 partitions=+partp8x8+partb8x8+parti8x8+parti4x4 mbd=2 trellis=1 mv4=1 subq=7 qmin=10 qcomp=0.6 qdiff=4 qmax=51 pass=1

melt -verbose -profile square_pal_wide $IN -consumer avformat:$OUT hq=1 acodec=libmp3lame ab=128k ar=44100 vcodec=mpeg4 threads=8 minrate=0 b=2000k aspect=1.7777 partitions=+partp8x8+partb8x8+parti8x8+parti4x4 mbd=2 trellis=1 mv4=1 subq=7 qmin=10 qcomp=0.6 qdiff=4 qmax=51 pass=2

