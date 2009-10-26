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
# from dateutil.parser import parse

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class add_dv(process):

    def one_dv(self, dir, dv ):
        
        pathname = os.path.join(dir,dv.filename)
        print pathname
        start=datetime.datetime.strptime(dv.filename,'%Y-%m-%d/%H:%M:%S.dv')
        # dt = dv.filename[:-3]
        # dt.replace('/',' ')
        st = os.stat(pathname)    
# get start from filesystem create timestamp
        # start=datetime.datetime.fromtimestamp( st.st_mtime )
        # start=parse(dt)
# use this to adjust for camera clock in wrong timezone
        # start -= datetime.timedelta(hours=2,minutes=0)
        if False and start.day==8:
            if dv.location.slug=='Holladay':
                print dv.location.slug
                start -= datetime.timedelta(hours=2,minutes=0)
            else:
                start -= datetime.timedelta(hours=2,minutes=37)

        frames = st.st_size/self.bpf
        duration = frames/self.fps ## seconds

        end = start + datetime.timedelta(seconds=duration)
        
        dv.start = start
        dv.end = end

        print dv,start,end
        if not self.options.test:
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

