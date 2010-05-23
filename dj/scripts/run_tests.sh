#!/bin/bash -xe

rm ../veyepar.db
if [ ! -e ../veyepar.db ]; then
  ../manage.py syncdb --noinput
fi
# make sample data: location, client, show, episode
python tests.py --client test_client --show test_show

# make dirs
python mkdirs.py --client test_client --show test_show

DIR=/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21
if [ ! -e $DIR/18:00:00.dv ]; then
 # put make some dv files in the source dir
 mkdir $DIR
 echo test 1 >t1.txt
 echo test 2 >t2.txt
 echo test 3 >t3.txt
 echo test 4 >t4.txt
 echo test 5 >t5.txt
# 1800,3600
 melt -profile dv_ntsc t1.txt out=180 -consumer avformat:$DIR/18:00:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t2.txt out=180 -consumer avformat:$DIR/18:01:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t3.txt out=180 -consumer avformat:$DIR/18:03:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t4.txt out=180 -consumer avformat:$DIR/18:04:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t5.txt out=180 -consumer avformat:$DIR/18:06:00.dv pix_fmt=yuv411p
 rm t?.txt
fi
 
# add the dv files to the db
python adddv.py --client test_client --show test_show
python tsdv.py --client test_client --show test_show
cp -a bling $DIR

if [ ! -e $DIR/18:00:00.png ]; then
  python mkthumbs.py --client test_client --show test_show
  python dvogg.py --client test_client --show test_show
fi
python assocdv.py --client test_client --show test_show
python enc.py --client test_client --show test_show --force
python post.py --client test_client --show test_show --force


