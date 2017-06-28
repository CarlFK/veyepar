#!/usr/bin/python

from datetime import datetime
from pprint import pprint

# copied from process.py
import os, sys, subprocess
# os.environ['DJANGO_SETTINGS_MODULE'] = 'dj.settings'
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "dj.settings")
sys.path.insert(0, '..' )

from django.conf import settings

import django
django.setup()

import socket

from main.models import Show # , Episode

fnames=[]
test_filename = 'tests.txt'
if os.path.exists(test_filename):
    call_list = open(test_filename).read().split('\n')
else:
    call_list = []

def callme_maybe(f):
    # if the function name is on the list, call it.
    # good way to disable it in the file is to # it, then "foo" not in ["# foo"]
    name = f.__name__
    # for when there is no list, create it.
    if name not in fnames: fnames.append(name)

    # if the name is on the list, call it.
    if name in call_list:
        print("running %s..." % name)
        return f
    else:
        def skip(*args,**kwargs):
            # print "skipping %s" % name
            return "skipped"
        return skip

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
            print("command returned", ret)
            print("cmd:", cmd)
        return ret


 @callme_maybe
 def make_test_user(self):
  from django.contrib.auth.models import User
  users=User.objects.all()
  if not users:
    user = User.objects.create_user( 'test', 'a@b.com', 'abc' )
    user.is_superuser=True
    user.is_staff=True
    user.save()
    print(user)
  return

 # @callme_maybe
 # always do this, cuz of self.episode=
 def setup_test_data(self):
  # make sample data: location, client, show, episode
  from main.views import make_test_data, del_test_data
  del_test_data()

  t=datetime(2010,5,21,0,0,4)
  self.episode=make_test_data(self.title, start_time = t)

  return

 # @callme_maybe
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
          self.show_dir, 'tmp', "%s.sh" % (self.slug) )
  return


 @callme_maybe
 def make_source_raw(self):
   """
 ` Make a set of source files.
   Similar to what voctomix/dvswitch creates (dir/filename date/time.dv)
   This takes the place of using an app to record an event.

   be sure the 2010-05-21 date
   matches start_date in make_sample_data above.
   """
   # get melt version to stick into video
   melt_outs = self.run_cmd(['melt', '--version'], True )
   melt_ver = melt_outs['serr'].split(b'\n')[0]
   melt_ver = str(melt_ver)
   print(melt_ver)

   dv_dir = self.show_dir + '/dv/test_loc/2010-05-21'
   if not os.path.exists(dv_dir): os.makedirs(dv_dir)

   # MELT_PARMS="-attach lines width=80 num=1 -attach lines width=2 num=10"
   text_file="source.txt"

   for i in range(5):
       # each file is 3 seconds long

       # encode the text file into a video file

       out_file="00_00_%02i.mp4" % (i*3)
       frames = 90
       parms={'input_file':text_file,
           'output_file':os.path.join(dv_dir,out_file),
           'format':self.options.dv_format,
           # 'format':"dv_ntsc_wide",
           'video_frames':frames,
           'audio_frames':frames}
       if i%2:
           parms['audio-track'] = "-producer noise"
           parms['bgcolour'] = "red"
       else:
           parms['audio-track'] = "static/goforward.wav"
           parms['bgcolour'] = "blue"

       print(parms)

       # make a text file to use as encoder input
       text = ["test %s - %s" % ( i, self.options.dv_format),
                  out_file,
                  melt_ver, datetime.now().ctime(),
                  '',
                  socket.gethostname()
              ]
       print(text)
       tf = open(text_file,'w')
       tf.write('\n'.join(text))
       tf.close()


       cmd = "melt \
-profile %(format)s \
 -audio-track %(audio-track)s out=%(audio_frames)s \
 -video-track %(input_file)s bgcolour=%(bgcolour)s out=%(video_frames)s \
meta.attr.titles=1 \
meta.attr.titles.markup=#timecode# \
-attach data_show dynamic=1 \
-consumer avformat:%(output_file)s \
pix_fmt=yuv411p" % parms
       self.run_cmd(cmd.split())

   return


 @callme_maybe
 def make_marks_file(self):
   """
   Make the file of cut click timestamps
   """
   pathname = self.show_dir + '/dv/test_loc/cut-list.log'
   open(pathname,'w').write(
   "2010-05-21/00_00_04\n2010-05-21/00_00_10\n")

 @callme_maybe
 def make_source_footer(self):
   """
 ` make a footer.png
   via a convoluted process, which has a side effect of more testing
   the process:
   create 1 line source.txt: ABCDEFG
   convert to 1 frame dv
   convert that frame to footer.png
   """

   tmp_dir = os.path.join(self.show_dir, 'tmp')
   assets_dir = os.path.join(self.show_dir, 'assets')
   text_file = os.path.join(tmp_dir, "source.txt")
   out_file = os.path.join(tmp_dir,"footer.mp4")
   parms={'input_file':text_file,
           'out_file':out_file,
           'text_file':text_file,
           'assets_dir':assets_dir,
           'format':self.options.dv_format,
           'video_frames':1,
           'audio_frames':1,
           'pix_fmt':'yuv411p',
           }
   print(parms)

   # make a text file to use as encoder input
   text = ["ABCDEFG", ]
   tf = open(text_file,'w')
   tf.write('\n'.join(text))
   tf.close()

   # create dv file from text and generated noise
   cmd = "melt \
 -profile %(format)s \
 -audio-track -producer noise out=%(audio_frames)s \
 -video-track %(input_file)s out=%(video_frames)s \
 -consumer avformat:%(out_file)s \
 strict=-2 \
 " % parms

   # pix_fmt=%(pix_fmt)s
   print(cmd)
   self.run_cmd(cmd.split())

   # grab a frame
   # make_test_data does:
   # client.credits="00000001.png"
   cmd = "mplayer \
           -frames 1 \
           -ao null \
           -vo png:outdir=%(assets_dir)s \
           %(out_file)s" % parms
   self.run_cmd(cmd.split())

   # "00000001.png"
   return

 @callme_maybe
 def add_raw(self):
  # add the dv files to the db
  import adddv
  print("add_raw starting...")
  p=adddv.add_dv()
  p.set_options(
    verbose=False)
  p.main()

  import tsdv
  p=tsdv.ts_rf()
  p.set_options(
    time_source="fn")
  p.main()

  return


 @callme_maybe
 def make_thumbs(self):
  # make thumbnails and preview ogv
  import mkthumbs
  p=mkthumbs.add_dv()
  p.main()

  import dv2ogv
  p=dv2ogv.mkpreview()
  p.main()

  return

 @callme_maybe
 def make_cut_list(self):
  # make cut list
  # this should associate clips2,3,4 with the test episode
  # from main.views import mk_cuts
  # cuts = mk_cuts(episode)
  print("assing dv...")
  import assocdv
  p=assocdv.ass_dv()
  p.main()
  print(p.cuts)
  count=p.cuts.count()
  selected=p.cuts.filter(apply=True).count()
  ret={'count':count, 'selected':selected}
  pprint(ret)
  cut=p.cuts[1]
  # cut=cuts[1]
  print(cut)
  # cut.start="0:0:1"
  # cut.end="0:0:10"
  # cut.apply=False
  # cut.save()

  return ret

 @callme_maybe
 def encode(self):
  # encode the test episode
  # create a title, use clips 2,3,4 as source, maybe a credits trailer
  import enc
  p=enc.enc()
  p.set_options(
    upload_formats=self.upload_formats,
    # rm_temp=False,
    debug_log=False)
  p.main()
  self.episode = p.episode
  return

 @callme_maybe
 def sync_rax(self):
  # gens low quality and audio viz
  print("sync_rax_lq...")
  import sync_rax
  p=sync_rax.SyncRax()
  p.set_options(
          verbose=False,
      assets=True,
      raw=True, low=True,
      cooked=True,
      audio_viz=True,
      replace=True, rsync=False
      )
  p.main()
  return

 @callme_maybe
 def ck_errors(self):
  # check for encoding errors
  # python ck_invalid.py -v --client test_client --show test_show --push
  import ck_invalid
  p=ck_invalid.ckbroke()
  p.main()
  return

 @callme_maybe
 def play_vid(self):
    # show the user what was made
    # todo: (speed up, we don't have all day)
    import play_vids
    p=play_vids.play_vids()
    p.main()

 @callme_maybe
 def post_blip(self):
  # post it to blip test account (password is in pw.py)
  import post_blip as post
  p=post.post()
  p.set_options(
      upload_formats=self.upload_formats,
      debug_log=True,
      )
  p.main()

  # post.py does: self.last_url = post_url.text
  # self.run_cmd(["firefox",p.last_url])
  return p.las

 @callme_maybe
 def push(self):
  # rsync to data center box
  import push
  p=push.push()
  p.set_options(
      upload_formats=self.upload_formats,
      )
  p.main()
  ret = p.ret

  return ret


 @callme_maybe
 def mk_audio_png(self):
      import mk_audio_png
      p=mk_audio_png.mk_audio_png()
      p.set_options(
              cloud_user='testact',
              upload_formats=self.upload_formats,
          )
      p.main()
      # ret = p.ret # retuns False cuz half baked

      ret = [os.path.exists(f) for f in p.files]

      return ret


 @callme_maybe
 def post_yt(self):
  # post it to youtube test account (password is in pw.py)
  import post_yt as post
  p=post.post()
  p.set_options(
      upload_formats=self.upload_formats,
      debug_log=True,
      replace=True,
      )
  p.private=True
  p.main()

  # post.py does: self.last_url = post_url.text
  # print p.last_url
  # self.run_cmd(["firefox",p.last_url])

  return p.last_url

 @callme_maybe
 def add_to_richard(self):
  # add the test to pyvideo.org:9000 test instance
  import add_to_richard
  p=add_to_richard.add_to_richard()
  p.set_options(
      upload_formats=self.upload_formats,
      )
  p.private=True
  p.main()
  ret = p.pvo_url
  return ret

 @callme_maybe
 def email_url(self):
  # add the test to pyvideo.org:9000 test instance
  import email_url
  p=email_url.email_url()
  ret = p.main()
  return ret


 @callme_maybe
 def tweet(self):
  # tell the world (test account)
  import tweet
  p=tweet.tweet()
  p.main()
  tweet_url = "http://twitter.com/#!/squid/status/%s" % (p.last_tweet["id"],)
  return tweet_url


 @callme_maybe
 def csv(self):
  # make csv and other data files
  import mkcvs
  p=mkcvs.csv()
  p.main()

  return


 @callme_maybe
 def ocr_test(self):
  # ocr an output file, check for ABCDEFG

  tmp_dir = os.path.join("/tmp/veyepar_test/")
  if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
  ext = self.upload_formats[0]

  filename = os.path.join(
          self.show_dir, ext, "%s.%s" % (self.episode.slug,ext) )
  parms = {
          "tmp_dir":tmp_dir,
          'filename':filename,
          }
  cmd = "mplayer \
    -ss 9 \
    -vf framestep=20 \
    -ao null \
    -vo pnm:outdir=%(tmp_dir)s \
    %(filename)s" % parms
  print(cmd)
  self.run_cmd(cmd.split())

  test_file = os.path.join(tmp_dir, "00000002.ppm" )
  gocr_outs = self.run_cmd(['gocr', test_file], True )
  text = gocr_outs['sout']

  # not sure what is tacking on the \n, but it is there, so it is here.
  acceptables = ["ABCDEFG\n","_BCDEFG\n"]
  print("acceptables:", acceptables)

  print("ocr results:", text)

  result = (text in acceptables)

  return result


 @callme_maybe
 def sphinx_test(self):
  # sphinx transcribe an output file, check for GO FORWARD TEN METERS
  # someday this will wget the m4v from blip to see what they made

  ext = self.upload_formats[0]
  filename = os.path.join(self.show_dir, ext, "%s.%s" % (self.episode.slug,ext) )

  tmp_dir = os.path.join("/tmp/veyepar_test/")
  if not os.path.exists(tmp_dir): os.makedirs(tmp_dir)
  wav_file = os.path.join(tmp_dir,'test.wav')
  raw_file = os.path.join(tmp_dir,'test.16k')
  ctl_file = os.path.join(tmp_dir,'test.ctl')

  parms = {
          'filename':filename,
          "wav_file":wav_file,
          "raw_file":raw_file,
          }

  cmd = "melt %(filename)s in=92 out=178 -consumer avformat:%(wav_file)s" % parms
  self.run_cmd(cmd.split())
  cmd = "sox %(filename)s -b 16 -r 16k -e signed -c 1 -t raw %(raw_file)s" % parms
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
          print(words)
          text = words[3:-2]
          result = ( text == ['GO', 'FORWARD', 'TEN', 'METERS'] )

          return result

 @callme_maybe
 def size_test(self):
     sizes = {
             'ogv':602392,
             'mp4':1636263,
             'webm':311874,
             }
     ret = True
     for ext in self.upload_formats:
         expected_size = sizes[ext]
         fullpathname = os.path.join( self.show_dir, ext,
                 "%s.%s" % (self.episode.slug, ext))
         st = os.stat(fullpathname)
         actual_size=st.st_size
         delta = expected_size - actual_size
         # is it off by more than some %
         tolerance = 2
         err = abs(delta * 100 / expected_size )
         if err > tolerance or self.options.verbose:
             ret = False
             print(ext)
             print("expectected: %15d" % expected_size)
             print("actual:      %15d" % actual_size)
             print("delta:       %15d" % delta)
             print("error:       %15d%%" % err)

     return ret



def main():
    result={}

    t=Run_Tests()
    # t.upload_formats=["webm",]
    t.upload_formats=["webm", "mp4",]
    # t.upload_formats=["flac",]
    t.title = "Let's make a Test"
    t.slug = "Lets_make_a_Test"

    t.make_test_user()
    t.setup_test_data()
    t.make_dirs() # don't skip this, it sets self.show_dir and stuff
    t.make_source_raw()
    t.make_marks_file()
    t.make_source_footer()
    t.add_raw()
    # t.make_thumbs() ## this jackes up gstreamer1.0 things, like mk_audio
    result['cuts'] = t.make_cut_list()
    t.sync_rax()
    ## test missing dv files
    # os.remove('/home/carl/Videos/veyepar/test_client/test_show/dv/test_loc/2010-05-21/00_00_03.dv')
    t.encode()
    # t.ck_errors() ## jacks gstreamer1.0 things...
    t.play_vid()
    result['push'] = t.push()
    result['mk_audio_png'] = t.mk_audio_png()
    result['url'] = t.post_yt()
    result['richard'] = t.add_to_richard()
    result['email'] = t.email_url()
    result['tweet'] = t.tweet()
    t.csv()
    result['ocr'] = t.ocr_test()
    # result['audio'] = t.sphinx_test() # sphinx no longer packaged :(
    result['sizes'] = t.size_test()

    print()
    print('test results', end=' ')
    pprint(result)

    if not os.path.exists(test_filename):
        print('\n'.join(fnames))
        open(test_filename,'w').write('\n'.join(fnames))

if __name__=='__main__':
    main()
