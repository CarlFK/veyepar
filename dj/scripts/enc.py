#!/usr/bin/python

# encodes to ogg

import os,sys,subprocess

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

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

class enc(process):

  ready_state = 2
  done_state = 3

  def process_ep(self,episode):
    print episode
    ret = False
    cl = Cut_List.objects.filter(episode=episode).order_by('sequence')
    if cl:
        oggpathname = os.path.join(self.show_dir, "ogg", "%s.ogg"%episode.slug)
        cmd="ffmpeg2theora --videoquality 5 -V 600 --audioquality 5 --speedlevel 0 --optimize --keyint 256 --channels 1".split()
        cmd+=['--output',oggpathname]
        if len(cl)==1:
            # use the raw dv file and ffmpeg2theora params to trim
            c=cl[0]
            if c.start: cmd+=['--starttime',str(time2s(c.start))]
            if c.end: cmd+=['--endtime',str(time2s(c.end))]
            dvpathname = os.path.join(self.episode_dir,c.raw_file.filename)
        else:
            # make a new dv file using just the frames to encode
            dvpathname = os.path.join(self.episode_dir,episode.slug+".dv")
            outf=open(dvpathname,'wb')
            for c in cl:
                print (c.raw_file.filename, c.start,c.end)
                rawpathname = os.path.join(self.episode_dir,c.raw_file.filename)
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
            ret = True
        else:
            print episode.id, episode.name
            print "transcode failed"
            print retcode, os.path.exists(oggpathname)
    else:
        print "No cutlist found."

    return ret

if __name__ == '__main__':
    p=enc()
    p.main()

