#!/usr/bin/python

"""
tsdv.py - timestamp dv
sets start/end times of dv files

Gets start from one of:
the file name (assumes yy_mm_dd/hh_mm_ss.dv format)
the file system time stamp, 
the first frame of the dv

duration (in seconds) based on file size / BBF*FPS 
last frame

"""

import  os
import datetime
# from dateutil.parser import parse

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class ts_dv(process):

    def one_dv(self, dir, dv, offset_hours ):

        """
        get the start of this clip
        dv.filename generally looks like this: 2012-01-14/10:01:34.dv
        dir is generally ~/Videos/veyepar/client/show/dv/room   
        parse the dir and filename strings.
        get filesystem_create also
        report differences
        generally use the parsed
        """
        
        pathname = os.path.join(dir,dv.filename)
        print pathname
        print dv.filename

        # get timestamp from filesystem
        # st = os.stat(pathname)    
        # ts_start=datetime.datetime.fromtimestamp( st.st_mtime )

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
        if offset_hours:
            start += datetime.timedelta(hours=offset_hours)

        # calc duration from size
        frames = dv.filesize/self.bpf
        seconds = frames/self.fps 

        # store duration in fancy human readable format (bad idea) 
        hms = seconds//3600, (seconds%3600)//60, seconds%60
        duration = "%02d:%02d:%02d" % hms

        dv.start = start
        dv.duration = duration

        print "start:\t%s" % start
        # print "ts_start:\t%s" % ts_start
        # print "delta:\t%s" % (ts_start - start)
        print

        if not self.options.test:
            dv.save()


    def one_loc(self,show, location,dir):
      for dv in Raw_File.objects.filter(show=show, location=location):
        print dv
        if not dv.start:
          self.one_dv(dir,dv, location.hours_offset)

    def one_show(self, show):
      self.set_dirs(show)
      locs = Location.objects.filter(show=show)
      if self.options.room:
          locs = locs.filter(name=self.options.room)
      for loc in locs:
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
    p=ts_dv()
    p.main()

