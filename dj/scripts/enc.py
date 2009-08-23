#!/usr/bin/python

# encodes to ogg

import optparse
import os,sys,subprocess

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
sys.path.insert(0, '..' )
import settings
settings.DATABASE_NAME="../vp.db"

from main.models import Show, Location, Episode, Raw_File, Cut_List

BPF=120000

def time2s(time):
    """ given 's.s' or 'h:m:s.s' returns s.s """
    if ':' in time:
        sec = reduce(lambda x, i: x*60 + i, 
            map(float, time.split(':')))  
    else:
        sec = float(time)
    return sec

def time2b(time,fps,bpf,default):
    """
    converts the time stored in the db (as blank, seconds or h:m:s.s)
    to the byte offset in the file.
    blank returns default, typically either 0 or filesize for start/end.
    fps is 25.0 for pal and 29.9 ntsc.
    bpf (bytes per frame) is 120000 for both.
    """
    if time:
        bytes = int(time2s(time)*fps)*bpf
    else:
        bytes = default
    return bytes

def enc_one(ep):
    root='/home/carl/Videos' # root dir of .dv files
    loc = ep.location
    show = loc.show
    root="%s/%s/%s" % (root,show.client.slug,show.slug)
    cl = Cut_List.objects.filter(episode=ep).order_by('sequence')
    if cl:
        dt=ep.start.strftime("%Y-%m-%d")
        dir="%s/dv/%s/%s" % (root,dt,loc.slug)
        cmd="ffmpeg2theora --videoquality 7 --audioquality 4 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd+=['--output',"%s/%s.ogg"%(show.slug,ep.slug)]
        if len(cl)==1:
            c=cl[0]
            if c.start: cmd+=['--starttime',str(time2s(c.start))]
            if c.end: cmd+=['--endtime',str(time2s(c.end))]
            pathname = "%s/%s"%(dir,c.raw_file.filename)
            cmd+=[pathname]
        else:
            outpathname = "/home/carl/temp/%s.dv"%ep.slug
            outf=open(outpathname,'wb')
            for c in cl:
                print (c.raw_file.filename, c.start,c.end)
                inpathname = "%s/%s"%(dir,c.raw_file.filename)
                inf=open(inpathname,'rb')
                inf.seek(time2b(c.start,29.9,BPF,0))
                size=os.fstat(inf.fileno()).st_size
                end = time2b(c.end,29.9,BPF,size)
                while inf.tell()<end:
                    outf.write(inf.read(BPF))
                inf.close()
            outf.close()
            cmd+=[outpathname]
        print ' '.join(cmd)
        p=subprocess.Popen(cmd).wait()
    else:
        print "No cutlist found."

    return 

def encshow(show):
    locs = Location.objects.filter(show=show)
    for loc in locs:
        episodes = Episode.objects.filter(location=loc)
        for ep in episodes:
             print ep.id, ep.name
             enc_one(ep)

def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-a', '--all' )
    parser.add_option('-s', '--show' )

    options, args = parser.parse_args()
    return options, args


def main():
    options, args = parse_args()

    if options.all:
        show = Show.objects.get(name='PyOhio09')
        encshow(show)
    elif options.show:
        show = Show.objects.get(name=options.show)
        encshow(show)
    else:
        episodes = Episode.objects.filter(id__in=args)
        for episode in episodes:
            enc_one(episode)
    

if __name__ == '__main__':
    main()

