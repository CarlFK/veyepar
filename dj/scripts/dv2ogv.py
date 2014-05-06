#!/usr/bin/python 

# makes .ogv of .dv files 
#   checks for existance, doesn't re-make the same one 
#   --rsync to upload to data center box

# use: 
#   dv2ogv.py 1234 - make thumb movies for episode# 1234


import  os
import subprocess

import rax_uploader

from process import process
from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class mkpreview(process):

    def rsync(self, loc_slug, f):

        host = self.options.cloud_host
        user = self.options.cloud_user
        dest_host = '%s@%s' % (user,host)
        dest_show_path = "/home/%s/Videos/veyepar/%s/%s" % (
                user, ep.show.client.slug, ep.show.slug, )
        dest_path = "%s/dv/%s/%s" % ( 
            dest_show_path,loc_slug,f['pathname'] )
        dest = "%s:%s" %( dest_host, dest_path )

        # dest = "veyepar@nextdayvideo.com:static/veyepar/pyconde/pyconde2013/dv/KOMED_Saal/2013-10-15"

        cmd = ['rsync',  '-tvP', '-e', 'ssh -p 222',
            f['pathname'], dest ]
        print cmd
        if not self.options.test:
            self.run_cmd(cmd)


    def one_dv(self,loc_dir,dv):
        print dv.filename, 
        src = os.path.join(loc_dir,dv.filename)
        dst = os.path.join(loc_dir,dv.basename()+'.ogv')
        print os.path.exists(dst) 
        if (not os.path.exists(dst)) or self.options.whack:
            cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --keyint 256".split()
            # cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --height 240 --framerate 2 --keyint 256 --channels 1".split()
            # cmd="ffmpeg2theora --videoquality 10 --videobitrate  16778 --optimize --audioquality 10 --audiobitrate 500 --keyint 1".split()
            cmd+=[ src, '-o', dst, ]
            # print ' '.join(cmd)
            if self.options.test:
                print "testing"
            else:
                p=subprocess.Popen(cmd).wait()
                
        if self.options.rsync:
            # self.rsync(dv.location.slug, {'pathname':dst})
            # self.file2cdn(dv.show, "titles/%s.svg" % (episode.slug))

            src = os.path.join(loc_dir,dv.basename()+'.ogv')
            if self.options.test:
                print "file2cdn src:", src
            else:
                self.file2cdn(dv.show, src )

        return
   
    def process_ep(self, ep):
        dir=os.path.join(self.show_dir,'dv',ep.location.slug)
        dvs = Raw_File.objects.filter(cut_list__episode=ep)
        for dv in dvs:
            self.one_dv(dir,dv)
        return True

    """
    def one_loc(self,location,dir):
      for dv in Raw_File.objects.filter(location=location):
          self.one_dv(dir,dv)

    def one_show(self, show):
      self.set_dirs(show)
      for loc in Location.objects.filter(show=show):
        dir=os.path.join(self.show_dir,'dv',loc.slug)
        if self.options.verbose: print show,loc,dir
        self.one_loc(loc, dir)

    def work(self):
        # find and process show
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)
            self.one_show(show)

        return

    """

    def add_more_options(self, parser):
        parser.add_option('-o', '--orphans', action='store_true',
          help='process orpahans (too?) (not implemented)' )
        parser.add_option('--rsync', action="store_true",
            help="upload to DS box.")



if __name__=='__main__': 
    p=mkpreview()
    p.main()

