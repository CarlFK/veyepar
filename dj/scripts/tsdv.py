#!/usr/bin/python

"""
tsdv.py - timestamp dv
sets start/end times of dv files

Gets start from one of:
the file system time stamp, 
the first frame of the dv
the file name (assumes hh_mm_ss.dv format)

duration (in seconds) based on file size / BBF*FPS 
last frame

"""

import  os
import datetime
# from dateutil.parser import parse

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class add_dv(process):

    def one_dv(self, dir, dv ):

        """
        get the start of this clip
        dv.filename generally looks like this: room/2012-01-14/10:01:34.dv
        parse the dir and filename strings.
        get filesystem_create also
        report differences
        generally use the parsed
        """
        
        pathname = os.path.join(dir,dv.filename)
        print pathname

        # get timestamp from filesystem
        st = os.stat(pathname)    
        ts_start=datetime.datetime.fromtimestamp( st.st_mtime )

        # parse string into datetime
        filename = dv.filename
        
        # remove extention
        filename,ext = os.path.splitext(filename)

        # dvswitch appends -n in the event of filename colisions. 
        # for start, dupe time is fine, so drop the -n for parsing 
        if filename[-2]=='-': filename = filename[:-2] 
  
        # for now, the last dir is the date, and the file is time:
        filename='/'.join(filename.split('/')[-2:])

        # swap : for _ (so either : or _ can be used in the filename)
        filename.replace(':','_')

        # parse
        start=datetime.datetime.strptime(filename,'%Y-%m-%d/%H_%M_%S')

        # adjust for clock in wrong timezone
        start += datetime.timedelta(hours=self.options.offset_hours)

        # calc duration from size
        frames = dv.filesize/self.bpf
        seconds = frames/self.fps 

        # store duration in fancy human readable format (bad idea) 
        hms = seconds//3600, (seconds%3600)//60, seconds%60
        duration = "%02d:%02d:%02d" % hms

        dv.start = start
        dv.duration = duration

        if not self.options.test:
            dv.save()


    def one_loc(self,show, location,dir):
      for dv in Raw_File.objects.filter(show=show, location=location):
        self.one_dv(dir,dv)

    def one_show(self, show):
      self.set_dirs(show)
      for loc in Location.objects.filter(show=show):
        dir=os.path.join(self.show_dir,'dv',loc.slug)
        print show,loc,dir
        self.one_loc(show, loc, dir)

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
        parser.add_option('--offset_hours', type="int",
           help="adjust time to deal with clock in wrong time zone.")

    def add_more_option_defaults(self, parser):
        parser.set_defaults(offset_hours=0)


if __name__=='__main__': 
    p=add_dv()
    p.main()

