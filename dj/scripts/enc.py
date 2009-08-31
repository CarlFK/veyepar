#!/usr/bin/python

# encodes to ogg

import optparse
import os,sys,subprocess
import datetime

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
        print time, len(time), [c for c in time]
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
    print ep.id, ep.name
    root='/home/carl/Videos/veyepar' # root dir of .dv files
    loc = ep.location
    show = loc.show
    client = show.client
    root=os.path.join(root,client.slug,show.slug)
    cl = Cut_List.objects.filter(episode=ep).order_by('sequence')
    if cl:
        dt=ep.start.strftime("%Y-%m-%d")
        src_dir=os.path.join(root, 'dv', loc.slug, dt)
        oggpathname = os.path.join(root, "ogg", "%s.ogg"%ep.slug)
        cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd+=['--output',oggpathname]
        if len(cl)==1:
            # use the raw dv file and ffmpeg2theora params to trim
            c=cl[0]
            if c.start: cmd+=['--starttime',str(time2s(c.start))]
            if c.end: cmd+=['--endtime',str(time2s(c.end))]
            dvpathname = os.path.join(src_dir,c.raw_file.filename)
        else:
            # make a new dv file using just the frames to encode
            dvpathname = os.path.join(src_dir,ep.slug+".dv")
            outf=open(dvpathname,'wb')
            for c in cl:
                print (c.raw_file.filename, c.start,c.end)
                rawpathname = os.path.join(src_dir,c.raw_file.filename)
                inf=open(rawpathname,'rb')
                inf.seek(time2b(c.start,29.9,BPF,0))
                size=os.fstat(inf.fileno()).st_size
                end = time2b(c.end,29.9,BPF,size)
                while inf.tell()<end:
                    outf.write(inf.read(BPF))
                inf.close()
            outf.close()
        
        cmd+=[dvpathname]
        print ' '.join(cmd)
        p=subprocess.Popen(cmd)
        p.wait()
        retcode=p.returncode
        if not retcode and os.path.exists(oggpathname):
            ep.state = 3
        else:
            print ep.id, ep.name
            print "transcode failed"
            print retcode, os.path.exists(oggpathname)
            # ep.state = 2
    else:
        print "No cutlist found."
    ep.save()

    return 
def enc_eps(episodes):
    for ep in episodes:
        if ep.state==2:
             # print ep.id, ep.name
             enc_one(ep)

def enc_show(show):
    locs = Location.objects.filter(show=show)
    for loc in locs:
        episodes = Episode.objects.filter(location=loc,state=2)
        enc_eps(episodes)


def parse_args():
    parser = optparse.OptionParser()
    parser.add_option('-a', '--all' )
    parser.add_option('-s', '--show' )
    parser.add_option('-d', '--day' )

    options, args = parser.parse_args()
    return options, args


def main():
    options, args = parse_args()

    if options.all:
        show = Show.objects.get(name='PyOhio09')
        enc_show(show)
    elif options.show:
        show = Show.objects.get(name=options.show)
        enc_show(show)
    elif options.day:
        show = Show.objects.get(name='PyOhio09')
        episodes = Episode.objects.filter(location__show=show,start__day=options.day)
        enc_eps(episodes)
    else:
        episodes = Episode.objects.filter(id__in=args)
        enc_eps(episodes)
    

if __name__ == '__main__':
    main()

