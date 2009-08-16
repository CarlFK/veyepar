#!/usr/bin/python

# Makes the dir tree for dvsink-file to put files into

import  os,sys

sys.path.insert(0, '..' )

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
import settings

from main.models import Show, Location

root='/home/juser/Videos'

show = Show.objects.get(name='PyOhio09')
print show
os.makedirs("%s/%s/dv" % (root,show.name))
for dt in ['2009-07-25','2009-07-26']:
    print dt
    dir="%s/%s/dv/%s" % (root,show.name,dt)
    os.mkdir(dir)
    locs = Location.objects.filter(show=show)
    for loc in locs:
         dir="%s/%s/dv/%s/%s" % (root,show.name,dt,loc.slug)
         print dir
         os.mkdir(dir)





