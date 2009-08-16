#!/usr/bin/python

# adds episodes from an external source, like a csv

import  os,sys
from csv import DictReader
from datetime import timedelta
from dateutil.parser import parse

sys.path.insert(0, '..' )

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings

from main.models import Show, Location, Episode

show = Show.objects.get(name='PyOhio09')
print show

# clear out previous runs for this show
Episode.objects.filter(location__show=show).delete()

reader = DictReader(open("sched.csv", "rb"))
{'Date': '2009-07-25', 'title': '#12 Getting Started With Django', 'Room': 'Auditorium', 'Time': '11:00:00 AM'}
seq=1
for row in reader:
    print row
    loc = Location.objects.get(show=show,name=row['Room'])
    print loc
    dt = row['Date']+' '+ row['Time']
    start=parse(dt)
    end=start+timedelta(minutes=65)
    print start,end
    ep = Episode(
       sequence=seq,
       location=loc, 
       name=row['title'], 
       start=start, end=end,
        ).save()
    seq+=1




