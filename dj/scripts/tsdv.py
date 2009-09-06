#!/usr/bin/python

"""
tsdv.py - timestamp dv
sets start/end times of dv files

Gets start from one of:
the file system time stamp, 
the first frame of the dv
the file name (assumes hh:mm:ss.dv format)

Gets end from:
start + duration based on file size / BBF*FPS
last frame

"""

import  os
import datetime

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class add_dv(process):

    def one_dv(self, dir, dv ):
        
        pathname = os.path.join(dir,dv.filename)
        print pathname
        st = os.stat(pathname)    
# get start from filesystem create timestamp
        start=datetime.datetime.fromtimestamp( st.st_mtime )

        # calc duration based on filesize
        frames = st.st_size/120000
        duration = frames/ 29.90 ## seconds

        end = start + datetime.timedelta(seconds=duration)
        
        dv.start = start
        dv.end = end

        print dv,start,end
        dv.save()


    def one_loc(self,location,dir):
      for dv in Raw_File.objects.filter(location=location):
        self.one_dv(dir,dv)

    def one_show(self, show):
      for loc in Location.objects.filter(show=show):
        dir=os.path.join(self.show_dir,'dv',loc.slug)
        print show,loc,dir
        self.one_loc(loc, dir)

if __name__=='__main__': 
    p=add_dv()
    p.main()

