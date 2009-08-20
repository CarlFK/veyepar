#!/usr/bin/python

# makes .ogg for all dv in a show

import  os,sys
import subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Show, Location, Episode, Raw_File, Cut_List

root='/home/carl/Videos' # root dir of .dv files
show = Show.objects.get(name='PyOhio09')
root="%s/%s/%s" % (root,show.client.slug,show.slug)

rfs=Raw_File.objects.filter(location__show=show)
for rf in rfs:
    print rf.basename()
    dt=rf.start.strftime("%Y-%m-%d")
    loc=rf.location
    dir="%s/dv/%s/%s" % (root,dt,loc.slug)
    print dir
    cmd="ffmpeg2theora --videoquality 1 --audioquality 2 --audiobitrate 32 --speedlevel 2 --width 360 --height 240 --framerate 2 --keyint 256 --channels 1".split()
    cmd+=[ '%s/%s'%(dir,rf.filename), '-o', '%s/%s.ogg'%(dir,rf.basename()) ]
    print ' '.join(cmd)
    p=subprocess.Popen(cmd).wait()


