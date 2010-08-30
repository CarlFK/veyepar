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
            cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --height 240 --framerate 2 --keyint 256 --channels 1".split()
            # cmd="ffmpeg2theora --videoquality 10 --videobitrate  16778 --optimize --audioquality 10 --audiobitrate 500 --keyint 1".split()
            cmd+=[ '-o', dst, src ]
            print ' '.join(cmd)
            p=subprocess.Popen(cmd).wait()
        return
   
    def process_ep(self, ep):
        dir=os.path.join(self.show_dir,'dv',ep.location.slug)
        dvs = Raw_File.objects.filter(cut_list__episode=ep)
        for dv in dvs:
            self.one_dv(dir,dv)
        return True


if __name__=='__main__': 
    p=mkpreview()
    p.main()

