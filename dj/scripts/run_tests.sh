#!/bin/bash -xe

MLT_VER=$(melt --version 2>&1 | grep MLT)

if [ -e ../../bin/activate ]; then
 . ../../bin/activate
fi

# rm ../veyepar.db
if [ ! -e ../veyepar.db ]; then
  ../manage.py syncdb --noinput
fi
# make sample data: location, client, show, episode
HOUR=$(python tests.py --client test_client --show test_show) 
# HOUR="00"
# make dirs
python mkdirs.py --client test_client --show test_show

BASE_DIR=~/Videos/veyepar/test_client/test_show 
DV_DIR=$BASE_DIR/dv/test_loc/2010-05-21
mkdir -p $DV_DIR
if [ ! -e $DIR/$HOUR:00:00.dv ]; then
 # put make some dv files in the source dir
 # mkdir $DV_DIR
 for i in {1..5} ; do 
   echo clip $i >t$i.txt; 
   date >> t$i.txt  
   echo $MLT_VER>>t$i.txt
 done 

 MELT_PARMS="-attach lines width=80 num=1 -attach lines width=2 num=10"
 MELT_PARMS=""
 melt -profile dv_ntsc t1.txt $MELT_PARMS out=180 -consumer avformat:$DV_DIR/$HOUR:00:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t2.txt $MELT_PARMS out=180 -consumer avformat:$DV_DIR/$HOUR:01:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t3.txt $MELT_PARMS out=30 -consumer avformat:$DV_DIR/$HOUR:03:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t4.txt $MELT_PARMS out=180 -consumer avformat:$DV_DIR/$HOUR:04:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t5.txt $MELT_PARMS out=30 -consumer avformat:$DV_DIR/$HOUR:06:00.dv pix_fmt=yuv411p
 rm t?.txt
fi
 
# add the dv files to the db
python adddv.py --client test_client --show test_show
python tsdv.py --client test_client --show test_show
cp -a bling $BASE_DIR

# make thumbnails and preview ogv
python mkthumbs.py --client test_client --show test_show
python dvogg.py --client test_client --show test_show

# make cut list
# this should associate clips2,3,4 with the test episode
python assocdv.py --client test_client --show test_show

# encode the test episode 
# create a title, use clips 2,3,4 as source, maybe a credits trailer 
python enc.py -v --client test_client --show test_show --force 
#  --upload-formats "flv ogv"

# show the user what was made (speed up, we don't have all day)
mplayer -speed 1 -osdlevel 3 $BASE_DIR/ogv/Test_Episode_0.ogv

# exit
# post it to blip test account (password is in pw.py)
python post.py -v --client test_client --show test_show --force \
 --blip-user veyepar_test
# --hidden=1

# tell the world (test account)
python tweet.py --client test_client --show test_show --force --test


