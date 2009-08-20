#!/usr/bin/python

# Adds the .dv files to the raw files table

import  os,sys
import datetime, time
from dateutil.parser import parse

import ocrdv
import dvdate

sys.path.insert(0, '..' )

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Show, Location, Episode, Raw_File, Cut_List

root='/home/carl/Videos' # root dir of .dv files


timetweak = -3600  # seconds to adjust file timestamp to reality (like timezones)

show = Show.objects.get(name='PyOhio09')
print show
root="%s/%s/%s/" % (root,show.client.slug,show.slug)

Raw_File.objects.filter(location__show=show).delete()

seq=1
for dt in ['2009-07-25','2009-07-26']:
    print dt
    locs = Location.objects.filter(show=show)
    for loc in locs:
         dir="%s/dv/%s/%s" % (root,dt,loc.slug)
         print dir
         files=os.listdir(dir)
         for dv in [f for f in files if f[-3:]=='.dv']:
             print dv
             pathname = "%s/%s"%(dir,dv)
             # get the timestamp from the dv (so from the camera)
             start = dvdate.get_timestamp(pathname)
             ts = time.mktime(start.timetuple())
             # set the file time stamp
             os.utime(pathname,(ts,ts))
             st = os.stat(pathname)
             # start = datetime.datetime.fromtimestamp( st.st_mtime ) 
             start += datetime.timedelta(seconds=timetweak)
             frames = st.st_size/120000
             duration = frames/ 29.90 ## seconds
             end = start + datetime.timedelta(seconds=duration) 
             print start, end, duration, duration/60
             orctext,img=ocrdv.ocrdv(pathname, frames)
             imgname = os.path.splitext(pathname)[0]+".jpg"
             img.save(imgname,'jpeg')

             rf, created = Raw_File.objects.get_or_create(
                 location=loc,
                 filename=dv,
                 start=start,end=end,
                 ocrtext=orctext)
             if not created: print "dupe"
             if parse(dt).date() != start.date(): 
                 print "wtf"
                 print parse(dt).date(), start.date()
             

             # find Episodes this may be a part of, add a cutlist record
             eps = Episode.objects.filter(location=loc, start__lte=end, end__gte=start)
             print eps
             for ep in eps:
                 Cut_List(episode=ep,raw_file=rf,sequence=seq).save()
             seq+=1

