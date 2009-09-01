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
    like slugify, but more file name friendly.
    """
    fn = text.replace(' ','_')
    fn = ''.join([c for c in fn if c.isalpha() or c.isdigit() or (c in '_') ])
    return fn

client,created = Client.objects.get_or_create(name='DjangoCon',slug="djcon")
show,created = Show.objects.get_or_create(name='DjangoCon 2008',slug="djc09",client=client)
print show

# clear out previous runs for this show
# Episode.objects.filter(location__show=show).delete()
# Location.objects.filter(show=show).delete()

reader = DictReader(open("sched.csv"))
seq=0
for row in reader:
    seq+=1
    print row

    loc,created = Location.objects.get_or_create(
        show=show,name=row['Room'],slug=fnify(row['Room']))
    name = row['title'] 
    
    # Remove #N from the start of PhOhio talk titles:
    if name.startswith('#'): name = ' '.join(name.split()[1:])

    dt = row['Date']+' '+ row['Time']
    start=parse(dt)
    end=start+timedelta(minutes=65)

    ep = Episode(
       sequence=seq,
       location=loc, 
       name=name,
       slug=fnify(name)
       primary=row['Link to talk'],
       authors=row['presenter(s)'], 
       start=start, end=end,
        )
    ep.save()

