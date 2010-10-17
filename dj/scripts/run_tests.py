#!/usr/bin/python

from datetime import datetime

# copied from process.py
import os, sys, subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
from django.conf import settings

from main.models import Show, Episode

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

  # hack to save some of these values for other tests
  # import process
  # p=process.process()
  self.show_dir = p.show_dir
  self.show=Show.objects.get(slug=p.options.show)
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

   # MELT_PARMS="-attach lines width=80 num=1 -attach lines width=2 num=10"
   text_file="source.txt"
   
   for i,l in enumerate(
         [('180','00:00'),
          ('180','01:58'),
          ('30','03:00'),
          ('180','04:58'),
          ('30','06:00'),]):

       # make a text file to use as encoder input
       text = ["test %s" % i, melt_ver, datetime.now().ctime()]
       tf = open(text_file,'wa')
       tf.write('\n'.join(text))
       tf.close()
       
       # encode the text file into .dv
       # this takes the place of using dvswitch to record an event.
       parms={'input_file':text_file, 
           'output_file':'%s/00:%s.dv' % (dv_dir,l[1]),
           'frames':l[0]}
       print parms
       cmd = "melt -profile dv_ntsc %(input_file)s \
out=%(frames)s \
meta.attr.titles=1 \
meta.attr.titles.markup=#timecode# \
-attach data_show dynamic=1 \
-consumer avformat:%(output_file)s pix_fmt=yuv411p" % parms
       self.run_cmd(cmd.split())

   self.run_cmd(['rm',text_file])
   cmd = ['cp', '-a', 'bling', self.show_dir ]
   self.run_cmd(cmd)

   return
 
 def add_dv(self):
  # add the dv files to the db
  import adddv
  p=adddv.add_dv()
  p.main()

  import tsdv
  p=tsdv.add_dv()
  p.main()

  return


 def make_thumbs(self):
  # make thumbnails and preview ogv
  import mkthumbs
  p=mkthumbs.add_dv()
  p.main()

  import dvogg
  p=dvogg.mkpreview()
  p.main()

  return


 def make_cut_list(self):
  # make cut list
  # this should associate clips2,3,4 with the test episode
  import assocdv
  p=assocdv.ass_dv()
  p.main()
  return


 def encode(self):
  # encode the test episode 
  # create a title, use clips 2,3,4 as source, maybe a credits trailer 
  # python enc.py -v --client test_client --show test_show --force 
  #  --upload-formats "flv ogv"
  import enc
  p=enc.enc()
  p.set_options(force=True, verbose=True, rm_temp=False)
  p.main()
  return

 def ck_errors(self):
  # check for encoding errors
  # python ck_invalid.py -v --client test_client --show test_show --push
  import ck_invalid
  p=ck_invalid.ckbroke()
  p.main()
  return

 def play_vid(self):
    # show the user what was made 
    # todo: (speed up, we don't have all day)
    import play_vids
    p=play_vids.play_vids()
    p.main()

 def post(self):
  # post it to blip test account (password is in pw.py)
  """
 python post.py -v --client test_client --show test_show \
 --blip-user veyepar_test
# --force \
# --hidden=1
  """
  import post
  p=post.post()
  p.main()
  return

 def tweet(self):
  # tell the world (test account)
  import tweet
  p=tweet.tweet()
  p.main()
  return


if __name__=='__main__':
    t=Run_Tests() 

    # t.make_test_user()
    # t.setup_test_data()
    t.make_dirs()
    # t.make_source_dvs()
    # t.add_dv()
    # t.make_thumbs()
    #t.make_cut_list()
    # t.encode()
    # t.ck_errors()
    t.play_vid()
    """
    t.tweet()
    t.post()
    t.tweet()
    """


