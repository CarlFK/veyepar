import errno
import sys
import time

import _inotify

wds = {}

def receive_event(event):
    mask = event["mask"]
    wd = event["wd"]
    if mask != _inotify.CLOSE_WRITE:
        print "weird mask", event
        return
    print "closed directory %s file %s" % (
        wds[wd],
        event['name'].strip(chr(0)))
                                           
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
