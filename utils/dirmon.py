import errno
import sys
import time
import os
import subprocess

import _inotify

wds = {}

def enc(dv):

    cmd="ffmpeg2theora --videoquality 4 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --keyint 256 ".split()
    cmd.append( dv )
    print ' '.join(cmd)

    p=subprocess.Popen(cmd).wait()
    return 


def process(dirname,filename):
    
    base,ext = os.path.splitext(filename)
    print(base,ext)
    if ext == ".dv":
        dvname = os.path.join(dirname,filename)
        print("encoding ffmpeg2theora {}".format(dvname))
        enc(dvname)
    else:
        print("skipping {}".format(filename))


def receive_event(event):
    mask = event["mask"]
    wd = event["wd"]
    if mask != _inotify.CLOSE_WRITE:
        print "weird mask", event
        return

    dirname = wds[wd]
    filename = event['name'].strip(chr(0))

    print "closed directory %s file %s" % (
        dirname,
        filename)
    
    process(dirname,filename)
                                           
if __name__ == '__main__':
    inotify_fd = _inotify.create()
    watch_directory = sys.argv[1]
    # we only want events where a file opened for write was
    # closed.
    wd = _inotify.add(inotify_fd, watch_directory, _inotify.CLOSE_WRITE)
    wds[wd] = watch_directory
    while True:
        time.sleep(1) # 1 second
        try:
            _inotify.read_event(inotify_fd, receive_event)
        except OSError as e:
            if e.errno != errno.EAGAIN:
                raise
