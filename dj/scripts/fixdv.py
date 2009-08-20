#!/usr/bin/python

# tweaks the time in the other direction

import  os,sys
import datetime, time

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Show, Location, Episode, Raw_File, Cut_List

timetweak = -3600  # seconds to adjust file timestamp to reality (like timezones)

show = Show.objects.get(name='PyOhio09')
rfs = Raw_File.objects.filter(location__show=show)
Cut_List.objects.all().delete()

for rf in rfs:
    rf.start += datetime.timedelta(seconds=3600*2)
    rf.end += datetime.timedelta(seconds=3600*2)
    rf.save()
    
    # find Episodes this may be a part of, add a cutlist record
    eps = Episode.objects.filter(
        location=rf.location, start__lte=rf.end, end__gte=rf.start)
    print eps
    seq=1
    for ep in eps:
        Cut_List(episode=ep,raw_file=rf,sequence=seq).save()
        seq+=1

