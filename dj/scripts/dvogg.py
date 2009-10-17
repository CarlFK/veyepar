#!/usr/bin/python 

# makes .ogg for all dv in a show

import  os
import subprocess

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class mkpreview(process):

    def one_file(self,loc_dir,rf):
        src = os.path.join(loc_dir,rf.filename)
        dst = os.path.join(loc_dir,rf.basename()+'.ogg')
        if not os.path.exists(dst):
            cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --height 240 --framerate 2 --keyint 256 --channels 1".split()
            cmd="ffmpeg2theora --videoquality 10 --videobitrate  16778 --optimize --audioquality 10 --audiobitrate 500 --keyint 1".split()
            cmd+=[ '-o', dst, src ]
            print ' '.join(cmd)
            p=subprocess.Popen(cmd).wait()
   
    def one_loc(self,location):
      """
      process files for this location
      """
      loc_dir=os.path.join(self.show_dir,'dv',location.slug)
      for rf in Raw_File.objects.filter(location=location):
          self.one_file(loc_dir, rf)

    def one_show(self, show):
      for loc in Location.objects.filter(show=show):
        print show,loc
        self.one_loc(loc)

if __name__=='__main__': 
    p=mkpreview()
    p.main()

