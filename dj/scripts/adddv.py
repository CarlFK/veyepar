#!/usr/bin/python

# Adds the .dv files to the raw files table

import  os,sys
import datetime
from dateutil.parser import parse

sys.path.insert(0, '..' )

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings

from main.models import Show, Location, Episode, Raw_File, Cut_List

root='/home/juser/Videos' # root dir of .dv files

timetweak = -3600  # seconds to adjust file timestamp to reality (like timezones)

show = Show.objects.get(name='PyOhio09')
print show

Raw_File.objects.filter(location__show=show).delete()

seq=1
for dt in ['2009-07-25','2009-07-26']:
    print dt
    locs = Location.objects.filter(show=show)
    for loc in locs:
         dir="%s/%s/dv/%s/%s" % (root,show.name,dt,loc.slug)
         print dir
         files=os.listdir(dir)
         for dv in files:
             print dv
             st = os.stat("%s/%s"%(dir,dv))
             start = datetime.datetime.fromtimestamp( st.st_mtime ) + \
               datetime.timedelta(seconds=timetweak)
             duration = st.st_size/(120000*29.90) ## seconds
             end = start + datetime.timedelta(seconds=duration) 
             print start, end, duration, duration/60
             rf, created = Raw_File.objects.get_or_create(
                 location=loc,
                 filename=dv,
                 start=start,end=end)
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

