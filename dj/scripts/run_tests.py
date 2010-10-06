#!/usr/bin/python

# copied from process.py
import os, sys, subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
from django.conf import settings

from datetime import datetime

class Run_Tests(object):

 def run_cmd(self,cmd, get_out=False):
        # print cmd
        print ' '.join(cmd)
        if get_out:
          p = subprocess.Popen(cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
          sout, serr = p.communicate()
          ret = dict( sout=sout, serr=serr, returncode=p.returncode)
        else:
          p = subprocess.Popen(cmd)
          p.wait()
          ret = dict( returncode=p.returncode)
        # p.stdin.write(it.buffer)
        # 2. write rest of image and get return values
        print ret
        if ret['returncode']: raise
        return ret


 def make_test_user(self):
  from django.contrib.auth.models import User
  users=User.objects.all()
  if not users:
    user = User.objects.create_user( 'test', 'test@example.com', 'abc' )
    user.is_superuser=True
    user.is_staff=True
    user.save()
    print user

  return

 def setup_test_data(self):
  # make sample data: location, client, show, episode
  from main.views import make_test_data, del_test_data
  del_test_data()
  ep_count=make_test_data()
  return

 def make_dirs(self):
  # create dirs for video files 
  import mkdirs
  p=mkdirs.mkdirs()
  p.main()
  self.show_dir = p.show_dir
  return

 def make_source_dvs(self):
   """ 
 ` make a set of .dv files
   similar to what dvswitch creates (dir/filename date/time.dv)
   """
   # get melt version to stick into video
   melt_outs = self.run_cmd(['melt', '--version'], True )
   melt_ver = melt_outs['serr'].split('\n')[0]
   print melt_ver

   dv_dir = self.show_dir + '/dv/test_loc/2010-05-21'
   if not os.path.exists(dv_dir): os.makedirs(dv_dir)

   # for i,l in enumerate([180,180,30,180,30]):
   
   start,length = 0,0
   for i,l in enumerate(
         [('180','00:00'),
          ('180','01:58'),
          ('30','03:00'),
          ('180','04:58'),
          ('30','06:00'),]):

       text = ["test %s" % i, melt_ver, datetime.now().ctime()]
       tf = open('source.txt','wa')
       tf.write('\n'.join(text))
       tf.close()
       
       cmd = "melt -profile dv_ntsc source.txt out=%s -consumer avformat:%s/00:%s.dv pix_fmt=yuv411p" % (l[0],dv_dir,l[1])
       self.run_cmd(cmd.split())

 
 """
 mkdir -p $DV_DIR
 if [ ! -e $DIR/$HOUR:00:00.dv ]; then
  # put make some dv files in the source dir
  # mkdir $DV_DIR
  for i in {1..5} ; do 
   echo clip $i >t$i.txt; 
   date >> t$i.txt  
   echo $MLT_VER>>t$i.txt

 MELT_PARMS="-attach lines width=80 num=1 -attach lines width=2 num=10"
 MELT_PARMS=""
 melt -profile dv_ntsc t1.txt $MELT_PARMS out=180 -consumer avformat:$DV_DIR/$HOUR:00:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t2.txt $MELT_PARMS out=180 -consumer avformat:$DV_DIR/$HOUR:01:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t3.txt $MELT_PARMS out=30 -consumer avformat:$DV_DIR/$HOUR:03:00.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t4.txt $MELT_PARMS out=180 -consumer avformat:$DV_DIR/$HOUR:04:58.dv pix_fmt=yuv411p
 melt -profile dv_ntsc t5.txt $MELT_PARMS out=30 -consumer avformat:$DV_DIR/$HOUR:06:00.dv pix_fmt=yuv411p
 rm t?.txt
 
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

 # check for encoding errors
 python ck_invalid.py -v --client test_client --show test_show --push

# show the user what was made (speed up, we don't have all day)
 mplayer -speed 1 -osdlevel 3 $BASE_DIR/ogv/Test_Episode_0.ogv

# exit
# post it to blip test account (password is in pw.py)
 python post.py -v --client test_client --show test_show \
 --blip-user veyepar_test
# --force \
# --hidden=1

# tell the world (test account)
 python tweet.py --client test_client --show test_show --force --test

 """

if __name__=='__main__':
    t=Run_Tests() 
    t.make_test_user()
    t.setup_test_data()
    t.make_dirs()
    t.make_source_dvs()

