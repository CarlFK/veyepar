#!/usr/bin/python

import datetime


import process
from main.models import fnify, Client, Show, Location, Episode, Raw_File, Cut_List 

from django.contrib.auth.models import User

users=User.objects.all()
if not users:
    user = User.objects.create_user( 'test', 'test@example.com', 'abc' )
    user.is_superuser=True
    user.is_staff=True
    user.save()

desc = """
Sample files and episode:  
file 0 and 4 are 1 min long, outside the range
file 1 and 3 are 2 min long, overlap the episode start/end
file 2 is 1 min long, inside the start/end
e=episode,r=raw files
time: 0  1  2  3  4  5  6  7
raws:  00 11111 22 33333 44
episode:     00000000
"""
 
loc,create = Location.objects.get_or_create(name='test loc',slug='test_loc')

# goofy code to remove all child recs
client,create = Client.objects.get_or_create(name='test client',slug='test_client')
client.delete()
client = Client.objects.create(name='test client',slug='test_client')

show = Show.objects.create(name='test show',slug='test_show',client=client)
show.locations.add(loc)

ep = Episode.objects.create(name='test episode',slug='test_episode',show=show,location=loc, sequence=1)

t=[datetime.datetime(2010,5,21,18,0)+datetime.timedelta(minutes=i) for i in range(8) ]

ep.description = desc
ep.authors = 'test author'
ep.start = t[2]
ep.duration = "00:03:00"
ep.save()
if ep.end != t[5]:
    print "episode end calc fail:"
    print ep.end
    print t[5]


e1=ep
e2=Episode.objects.create(name='episode 2',show=show,location=loc )
e2.save()
e3=Episode.objects.create(name='episode 3',show=show,location=loc )
e3.save()

# e1.get_previous_by_start()
# e1.get_next_by_start()
e2.get_next_by_start()
# e2.get_previous_by_start()
# e3.get_next_by_start()
e3.get_previous_by_start()

prev_episode = Episode.objects.filter(start__isnull=True).order_by('id').reverse()[0]
print prev_episode

prev_episode = Episode.objects.filter(start__isnull=False).order_by('id').reverse()[0]
print prev_episode
