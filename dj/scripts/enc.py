#!/usr/bin/python

# encodes to ogg

import  os,sys,subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Show, Location, Episode, Raw_File, Cut_List

show = Show.objects.get(name='PyOhio09')
# os.mkdir(show.slug)
root='/home/carl/Videos' # root dir of .dv files
root="%s/%s/%s" % (root,show.client.slug,show.slug)

locs = Location.objects.filter(show=show)
for loc in locs:
    episodes = Episode.objects.filter(location=loc)
    for ep in episodes:
        cl = Cut_List.objects.filter(episode=ep).order_by('sequence')
        if cl:
            dt=ep.start.strftime("%Y-%m-%d")
            dir="%s/dv/%s/%s" % (root,dt,loc.slug)
            cmd="ffmpeg2theora --videoquality 7 --audioquality 4 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
            if len(cl)==1:
                c=cl[0]
                if c.start: cmd+=['--starttime',c.start]
                if c.end: cmd+=['--endtime',c.end]
                cmd+=['--output',"%s/%s.ogg"%(show.slug,ep.slug)]
                pathname = "%s/%s"%(dir,c.raw_file.filename)
                cmd+=[pathname]
                print ' '.join(cmd)
                p=subprocess.Popen(cmd).wait()
            else:
                print ep.id, ep.name
                for c in cl:
                    pathname = "%s/%s"%(dir,c.raw_file.filename)
                    print pathname, c.start,c.end



