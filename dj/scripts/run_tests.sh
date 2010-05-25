#!/bin/bash -xe

# rm ../veyepar.db
if [ ! -e ../veyepar.db ]; then
  ../manage.py syncdb --noinput
fi
# make sample data: location, client, show, episode
python tests.py --client test_client --show test_show

# make dirs
python mkdirs.py --client test_client --show test_show

BASE_DIR=~/Videos/veyepar/test_client/test_show 
DV_DIR=$BASE_DIR/dv/test_loc/2010-05-21
if [ ! -e $DIR/18:00:00.dv ]; then
 # put make some dv files in the source dir
 # mkdir $DV_DIR
 for i in {1..5} ; do 
   echo test $i >t$i.txt; 
   date >> t$i.txt
 done 
 melt -profile dv_ntsc t1.txt out=180 -consumer avformat:$DV_DIR/18:00:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t2.txt out=180 -consumer avformat:$DV_DIR/18:01:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t3.txt out=30 -consumer avformat:$DV_DIR/18:03:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t4.txt out=180 -consumer avformat:$DV_DIR/18:04:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t5.txt out=30 -consumer avformat:$DV_DIR/18:06:00.dv pix_fmt=yuv411p
 rm t?.txt
fi
 
# add the dv files to the db
python adddv.py --client test_client --show test_show
python tsdv.py --client test_client --show test_show
cp -a bling $BASE_DIR

if [ ! -e $DV_DIR/18:00:00.png ]; then
  python mkthumbs.py --client test_client --show test_show
  python dvogg.py --client test_client --show test_show
fi
python assocdv.py --client test_client --show test_show
python enc.py --client test_client --show test_show --force

mplayer -speed 4 -osdlevel 3 $BASE_DIR/ogv/test_episode.ogv

python post.py --client test_client --show test_show --force --hidden=1
python tweet.py --client test_client --show test_show --force --test


