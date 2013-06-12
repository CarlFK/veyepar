#!/usr/bin/python 

# makes .ogv for all dv in a show

import  os
import subprocess

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class mkpreview(process):

    def one_dv(self,loc_dir,dv):
        src = os.path.join(loc_dir,dv.filename)
        dst = os.path.join(loc_dir,dv.basename()+'.ogv')
        if not os.path.exists(dst):
            cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --keyint 256".split()
            # cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --height 240 --framerate 2 --keyint 256 --channels 1".split()
            # cmd="ffmpeg2theora --videoquality 10 --videobitrate  16778 --optimize --audioquality 10 --audiobitrate 500 --keyint 1".split()
            cmd+=[ src, '-o', dst, ]
            print ' '.join(cmd)
            p=subprocess.Popen(cmd).wait()
        return
   
    """
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
        """
        find and process show
        """
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)
            self.one_show(show)

        return

    def add_more_options(self, parser):
        parser.add_option('-o', '--orphans', action='store_true',
          help='csv file' )


if __name__=='__main__': 
    p=mkpreview()
    p.main()

