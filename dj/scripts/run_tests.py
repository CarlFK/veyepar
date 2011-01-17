#!/usr/bin/python

from datetime import datetime

# copied from process.py
import os, sys, subprocess
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
from django.conf import settings

import socket

from main.models import Show, Episode

class Run_Tests(object):

 def run_cmd(self,cmd, get_out=False):

        log_text = ' '.join(cmd)
        print log_text
        open(self.sh_pathname,'a').write(log_text+'\n')

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
    user = User.objects.create_user( 'test', 'a@b.com', 'abc' )
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
  self.show_dir = p.show_dir
  self.show=Show.objects.get(slug=p.options.show)
  self.options = p.options
  self.sh_pathname = os.path.join( self.show_dir, 'tmp', "Test_Episode.sh" )
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
   
   for i in range(5):
       # each file is 3 seconds long

       # encode the text file into .dv
       # this takes the place of using dvswitch to record an event.
       #  works: "melt -profile dv_ntsc

       out_file="00:00:%02i.dv" % (i*3)
       parms={'input_file':text_file, 
           'output_file':os.path.join(dv_dir,out_file),
           'format':"dv_%s" % (self.options.dv_format),
           'video_frames':30 * 3,
           'audio_frames':30 * 3 * (i%2)}
       print parms

       # make a text file to use as encoder input
       text = ["test %s - %s" % ( i, self.options.dv_format),
                  out_file,
                  melt_ver, datetime.now().ctime(),
                  '',
                  socket.gethostname()
              ]
       print text
       tf = open(text_file,'w')
       tf.write('\n'.join(text))
       tf.close()
       
       cmd = "melt \
-profile %(format)s \
 -audio-track -producer noise out=%(audio_frames)s \
 -video-track %(input_file)s out=%(video_frames)s \
meta.attr.titles=1 \
meta.attr.titles.markup=#timecode# \
-attach data_show dynamic=1 \
-consumer avformat:%(output_file)s \
pix_fmt=yuv411p" % parms
       self.run_cmd(cmd.split())

   # self.run_cmd(['rm',text_file])
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
  print p.cuts
  cut=p.cuts[1]
  print cut
  # cut.start="0:0:1"
  # cut.end="0:0:10"
  # cut.save()
  return


 def encode(self):
  # encode the test episode 
  # create a title, use clips 2,3,4 as source, maybe a credits trailer 
  # python enc.py -v --client test_client --show test_show --force 
  #  --upload-formats "flv ogv"
  import enc
  p=enc.enc()
  
  p.set_options(force=True, verbose=True, 
    upload_formats=self.upload_formats, 
    rm_temp=False, debug_log=True)
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
  p.set_options(force=True, verbose=True, 
      upload_formats=self.upload_formats,
      debug_log=True)
  p.main()
  # self.url = p.last_url
  self.run_cmd(["firefox",p.last_url])
  return

 def tweet(self):
  # tell the world (test account)
  import tweet
  p=tweet.tweet()
  p.set_options(force=True, verbose=True, )
  p.main()
  return



if __name__=='__main__':

    t=Run_Tests() 
    t.upload_formats="flv ogv m4v mp3"

    t.make_test_user()
    t.setup_test_data()
    t.make_dirs() # don't skip this, it sets self.show_dir and stuff
    t.make_source_dvs()
    t.add_dv()
    t.make_thumbs()
    t.make_cut_list()
    t.encode()
    t.ck_errors()
    t.play_vid()
    t.post()
    t.tweet()


