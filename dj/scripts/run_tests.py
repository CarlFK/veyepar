#!/usr/bin/python

from datetime import datetime

# copied from process.py
import os, sys, subprocess
# os.environ['DJANGO_SETTINGS_MODULE'] = 'dj.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj.settings")
sys.path.insert(0, '..' )

from django.conf import settings

import socket

from main.models import Show # , Episode

class Run_Tests(object):

 def run_cmd(self, cmd, get_out=False):

        log_text = ' '.join(cmd)
        # print log_text
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

        if ret['returncode']: 
            ret['command'] = cmd
            print "command returned", ret
            print "cmd:", cmd
            raise
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
  self.ep=make_test_data(self.title)
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
  self.sh_pathname = os.path.join( 
          self.show_dir, 'tmp', "%s.sh" % (self.title) )
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

       out_file="00_00_%02i.dv" % (i*3)
       frames = 90
       parms={'input_file':text_file, 
           'output_file':os.path.join(dv_dir,out_file),
           'format':"dv_%s" % (self.options.dv_format),
           'video_frames':frames,
           'audio_frames':frames}
       if i%2:
           parms['audio-track'] = "-producer noise"
       else:
           parms['audio-track'] = "static/goforward.wav" 

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
 -audio-track %(audio-track)s out=%(audio_frames)s \
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
 

 def make_source_footer(self):
   """ 
 ` make a footer.png 
   via a convoluted process, which has a side effect of more testing
   the process:
   create 1 line source.txt: ABCDEFG
   convert to 1 frame dv
   convert that frame to footer.png
   """

   # dv_dir = os.path.join(self.show_dir,'dv', 'test_loc','2010-05-21')
   tmp_dir = os.path.join(self.show_dir, 'tmp')
   bling_dir = os.path.join(self.show_dir, 'bling')
   text_file = os.path.join(tmp_dir, "source.txt")
   dv_file = os.path.join(tmp_dir,"footer.dv") 
   parms={'input_file':text_file, 
           'dv_file':dv_file,
           'text_file':text_file,
           'bling_dir':bling_dir,
           'format':"dv_%s" % (self.options.dv_format),
           'video_frames':1,
           'audio_frames':1 }
   print parms

   # make a text file to use as encoder input
   text = ["ABCDEFG", ]
   tf = open(text_file,'w')
   tf.write('\n'.join(text))
   tf.close()
   
   cmd = "melt \
 -profile %(format)s \
 -audio-track -producer noise out=%(audio_frames)s \
 -video-track %(input_file)s out=%(video_frames)s \
 -consumer avformat:%(dv_file)s \
 pix_fmt=yuv411p" % parms
   self.run_cmd(cmd.split())

   cmd = "mplayer \
           -frames 1 \
           -ao null \
           -vo png:outdir=%(bling_dir)s \
           %(dv_file)s" % parms
   self.run_cmd(cmd.split())

   # "00000001.png"
   return 
 
 def add_dv(self):
  # add the dv files to the db
  import adddv
  p=adddv.add_dv()
  p.main()

  import tsdv
  p=tsdv.ts_dv()
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
  # cut.apply=False
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
    rm_temp=False, debug_log=False)
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

 def post_blip(self):
  # post it to blip test account (password is in pw.py)
  """
 python post.py -v --client test_client --show test_show \
 --blip-user veyepar_test
# --force \
# --hidden=1
  """
  import post_blip as post
  p=post.post()
  p.set_options(force=True, verbose=True, 
      upload_formats=self.upload_formats,
      debug_log=True,
      host_user="veyepar_test",
      )
  p.main()
 
  # post.py does: self.last_url = post_url.text
  # self.run_cmd(["firefox",p.last_url])
  return p.las

 def post_yt(self):
  # post it to youtube test account (password is in pw.py)
  """
 python post.py -v --client test_client --show test_show \
 --blip-user veyepar_test
# --force \
# --hidden=1
  """
  import post_yt as post
  p=post.post()
  p.set_options(force=True, verbose=True, 
      upload_formats=['mp4', "dv"],
      debug_log=True,
      host_user="test",
      )
  p.private=True
  p.main()
 
  # post.py does: self.last_url = post_url.text
  # print p.last_url
  # self.run_cmd(["firefox",p.last_url])

  return p.last_url

 def add_to_richard(self):
  # add the test to pyvideo.org:9000 test instance
  import add_to_richard
  p=add_to_richard.add_to_richard()
  p.set_options(force=True, verbose=True, 
      upload_formats=['mp4'],
      host_user="test",
      )
  p.private=True
  p.main()
  ret = p.pvo_url

  return ret

 def email_url(self):
  # add the test to pyvideo.org:9000 test instance
  import email_url
  p=email_url.email_url()
  p.set_options(force=True, verbose=True, 
      host_user="test",
      )
  ret = p.main()

  return ret


 def tweet(self):
  # tell the world (test account)
  import tweet
  p=tweet.tweet()
  p.set_options(force=True, verbose=True, lag=0, )
  p.main()
  tweet_url = "http://twitter.com/#!/squid/status/%s" % (p.last_tweet["id"],)
  return tweet_url


 def csv(self):
  # make csv and other data files
  import mkcvs
  p=mkcvs.csv()
  p.main()

  return


 def ocr_test(self):
  # ocr an output file, check for ABCDEFG
  # someday this will wget the m4v from blip to see what they made

  tmp_dir = os.path.join("/tmp/veyepar_test/")
  if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)

  blip_file = os.path.join(self.show_dir, 'mp4', "%s.mp4" % (self.title,) )
  # blip_file = "Veyepar_test-TestEpisode897.m4v"
  parms = {
          "tmp_dir":tmp_dir,
          'blip_file':blip_file,
          }
  cmd = "mplayer \
    -ss 12 \
    -vf framestep=20 \
    -ao null \
    -vo pnm:outdir=%(tmp_dir)s \
    %(blip_file)s" % parms
  print cmd
  self.run_cmd(cmd.split())

  test_file = os.path.join(tmp_dir, "00000006.ppm" )
  gocr_outs = self.run_cmd(['gocr', test_file], True )
  text = gocr_outs['sout']
  print text
  
  # not sure what is tacking on the \n, but it is there, so it is here.
  result = (text in ["ABCDEFG\n","_BCDEFG\n"])

  return result


 def sphinx_test(self):
  # sphinx transcribe an output file, check for GO FORWARD TEN METERS
  # someday this will wget the m4v from blip to see what they made

  blip_file = os.path.join(self.show_dir, 'mp4', "%s.mp4" % (self.title,) )
  # blip_file = "Veyepar_test-TestEpisode897.m4v"

  tmp_dir = os.path.join("/tmp/veyepar_test/")
  if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
  wav_file = os.path.join(tmp_dir,'test.wav')
  raw_file = os.path.join(tmp_dir,'test.16k')
  ctl_file = os.path.join(tmp_dir,'test.ctl')

  parms = {
          'blip_file':blip_file,
          "wav_file":wav_file,
          "raw_file":raw_file,
          }

  cmd = "melt %(blip_file)s in=92 out=178 -consumer avformat:%(wav_file)s" % parms
  self.run_cmd(cmd.split())
  cmd = "sox %(wav_file)s -b 16 -r 16k -e signed -c 1 -t raw %(raw_file)s" % parms
  self.run_cmd(cmd.split())

  # open(ctl_file,'w').write(raw_file)
  open(ctl_file,'w').write('test')
  parms = {
          'HMM':'/usr/share/sphinx2/model/hmm/6k',
          'TURT':'/usr/share/sphinx2/model/lm/turtle',
          'TASK':tmp_dir,
          "ctl_file":ctl_file,
          }

  cmd = """sphinx2-continuous -verbose 9 -adcin TRUE -adcext 16k -ctlfn %(ctl_file)s -ctloffset 0 -ctlcount 100000000 -datadir %(TASK)s -agcmax TRUE -langwt 6.5 -fwdflatlw 8.5 -rescorelw 9.5 -ugwt 0.5 -fillpen 1e-10 -silpen 0.005 -inspen 0.65 -top 1 -topsenfrm 3 -topsenthresh -70000 -beam 2e-06 -npbeam 2e-06 -lpbeam 2e-05 -lponlybeam 0.0005 -nwbeam 0.0005 -fwdflat FALSE -fwdflatbeam 1e-08 -fwdflatnwbeam 0.0003 -bestpath TRUE -kbdumpdir %(TASK)s -lmfn %(TURT)s/turtle.lm -dictfn %(TURT)s/turtle.dic -ndictfn %(HMM)s/noisedict -phnfn %(HMM)s/phone -mapfn %(HMM)s/map -hmmdir %(HMM)s -hmmdirlist %(HMM)s -8bsen TRUE -sendumpfn %(HMM)s/sendump -cbdir %(HMM)s """ % parms

  # print cmd
  sphinx_outs = self.run_cmd(cmd.split(),True)
  text = sphinx_outs['serr']
  # print text
  for line in text.split('\n'):
      if "BESTPATH" in line:
          words = line.split()
          print words
          text = words[3:-2]
          result = ( text == ['GO', 'FORWARD', 'TEN', 'METERS'] )

          return result
  
 def size_test(self):
     sizes = [
             ('ogv',602392),
             ('mp4',1636263),
             ]
     ret = True
     for size in sizes:
         ext,expected_size = size
         fullpathname = os.path.join( self.show_dir, ext,
                 "%s.%s" % (self.title, ext))
         st = os.stat(fullpathname)
         actual_size=st.st_size
         delta = expected_size - actual_size
         # is it off by more than some %
         tolerance = 2
         err = abs(delta * 100 ) / expected_size
         if err > tolerance:
             ret = False
             print ext
             print "expectected: %15d" % expected_size
             print "actual:      %15d" % actual_size
             print "delta:       %15d" % delta
             print "error:       %15d%%" % err

     return ret



def main():

    result={}

    t=Run_Tests() 
    t.upload_formats=["mp4"]
    # t.upload_formats=["ogv","mp4"]
    t.title = "Let's make a Test"

    # t.make_test_user()
    # t.setup_test_data()
    t.make_dirs() # don't skip this, it sets self.show_dir and stuff
    # t.make_source_dvs()
    # t.make_source_footer()
    # t.add_dv()
    # t.make_thumbs()
    # t.make_cut_list()
    ## test missing dv files
    # os.remove('/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21/00_00_03.dv')
    t.encode()
    # t.ck_errors()
    # t.play_vid()
    # result['url'] = t.post_yt()
    # result['richard'] = t.add_to_richard()
    # result['email'] = t.email_url()
    # result['tweet'] = t.tweet()
    # t.csv()
    # result['video'] = t.ocr_test()
    # result['audio'] = t.sphinx_test()
    # result['sizes'] = t.size_test()

    print 
    print 'test results', result

if __name__=='__main__':
    main()
