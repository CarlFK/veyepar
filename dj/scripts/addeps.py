#!/usr/bin/python

# adds episodes from an external source, like a csv

import  os,sys
from csv import DictReader
from datetime import timedelta
from dateutil.parser import parse

sys.path.insert(0, '..' )

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings
print settings.DATABASE_NAME
settings.DATABASE_NAME="../vp.db"

from main.models import Client, Show, Location, Episode

Client.objects.all().delete()
Show.objects.all().delete()
client,created = Client.objects.get_or_create(name='PyOhio',slug="pyohio")
show,created = Show.objects.get_or_create(name='PyOhio09',slug="pyohio09",client=client)
print show

# clear out previous runs for this show
Episode.objects.filter(location__show=show).delete()
Location.objects.filter(show=show).delete()

reader = DictReader(open("sched.csv", "rb"))
{'Date': '2009-07-25', 'title': '#12 Getting Started With Django', 'Room': 'Auditorium', 'Time': '11:00:00 AM'}
seq=1
for row in reader:
    print row
    location= ''.join([c for c in row['Room'] if c.isalpha() or c.isdigit()]).lower()
    loc,created = Location.objects.get_or_create(show=show,name=row['Room'],slug=location)
    print loc
    name = row['title'] 
    if name.startswith('#'): name = ' '.join(name.split()[1:])
    slug = ''.join([c for c in name if c.isalpha() or c.isdigit()]).lower()
    dt = row['Date']+' '+ row['Time']
    start=parse(dt)
    end=start+timedelta(minutes=65)
    print start,end
    ep = Episode(
       sequence=seq,
       location=loc, 
       name=name,
       slug=slug,
       authors=row['presenter(s)'], 
       start=start, end=end,
        ).save()
    seq+=1

