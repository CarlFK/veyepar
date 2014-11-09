# dirmon.py - monitors a dir for new .dv files.
import argparse
import errno
import sys
import time
import os
import subprocess
import datetime 
import ConfigParser
import socket


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

def find_dir(default_dir):

    hostname=socket.gethostname() 

    config = ConfigParser.RawConfigParser()
    files=config.read([
        os.path.expanduser('~/veyepar/dj/scripts/veyepar.cfg'),
        os.path.expanduser('~/veyepar.cfg')])

    if files:
        d=dict(config.items('global'))
        client = d['client']
        show = d['show']
        loc = d.get('room',hostname)
        dv_dir = os.path.join( 'veyepar', client, show, 'dv', loc )
    else:
        dv_dir = os.path.join( 'dv', hostname )

    dv_dir = os.path.join( 
            os.path.expanduser('~/Videos'), 
            dv_dir,
            datetime.datetime.now().strftime('%Y-%m-%d'))

    print("Checking for: {}".format(dv_dir))
    if os.path.exists(dv_dir):
        print("found.")
        ret = dv_dir
    else:
        print("not found, using fallback {}".format(default_dir))
        ret = default_dir

    return ret

def parse_args():
    parser = argparse.ArgumentParser()
    args = parser.parse_args()

def main():
    args = parse_args()

    inotify_fd = _inotify.create()
    watch_directory = find_dir(".") 
    print("Monitoring: {}".format(watch_directory))

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

if __name__ == '__main__':
    main()
