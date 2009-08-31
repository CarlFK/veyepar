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

def fnify(text):
    """
    file_name_ify - make a file name out of text, like a talk title.
    convert spaces to _, remove junk like # and quotes.
    """
    fn = text.replace(' ','_')
    fn = ''.join([c for c in fn if c.isalpha() or c.isdigit() or (c in '_') ])
    return fn

# Client.objects.all().delete()
# Show.objects.all().delete()
client,created = Client.objects.get_or_create(name='PyOhio',slug="pyohio")
show,created = Show.objects.get_or_create(name='PyOhio09',slug="pyohio09",client=client)
print show

# clear out previous runs for this show
# Episode.objects.filter(location__show=show).delete()
# Location.objects.filter(show=show).delete()

reader = DictReader(open("sched.csv", "rb"))
{'Date': '2009-07-25', 'title': '#12 Getting Started With Django', 'Room': 'Auditorium', 'Time': '11:00:00 AM'}
seq=1
for row in reader:
    print row
    location= ''.join([c for c in row['Room'] if c.isalpha() or c.isdigit()]).lower()
    loc,created = Location.objects.get_or_create(show=show,name=row['Room'],slug=location)
    print loc
    name = row['title'] 
    
    # Remove #N from the start of PhOhio talk titles:
    if name.startswith('#'): name = ' '.join(name.split()[1:])
    slug = fnify(name)

    dt = row['Date']+' '+ row['Time']
    start=parse(dt)
    end=start+timedelta(minutes=65)
    # print start,end
    ep = Episode(
       sequence=seq,
       location=loc, 
       name=name,
       slug=slug,
       primary=row['Link to talk'],
       authors=row['presenter(s)'], 
       start=start, end=end,
        )
    # ep.save()
    """
    eps = Episode.objects.filter(slug=slug)
    if eps:
        if len(eps)==1: 
            if row['Link to talk']:
                eps[0].primary = row['Link to talk']
                eps[0].save()
    else:
        print eps
    """
    seq+=1

