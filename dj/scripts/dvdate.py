#!/usr/bin/python

# dvdate.py - gets date of .dv file - shells out to dvgrab

import os, subprocess
import time
from dateutil.parser import parse

dvfile = 'pyohio.dv'

def get_timestamp(dvfilename):
    while True:
        p = subprocess.Popen( ['dvgrab', '-d', '1', '-I', dvfilename, '/tmp/dvg'], stderr=subprocess.PIPE ) 
        time.sleep(10)
        if p.poll() is None:
            print "die!"
            # p.send_signal()
            p.kill()
            print "dead?"
        else:
            out,err = p.communicate()
            subprocess.Popen(['pkill','-9','dvgrab']).wait()
            time.sleep(10)
            break

    try:
        text = err.split('\n')
        for info in text:
            if "timecode" in info: break
        # pos = text.index('Capture Started')+1 # 2 or 3 depending on if 'End of pipe' sneaked in
        info = info.split()
        pos = info.index('date')+1 # +1 becaue the date/time come after it
    except:
        print out, err
        print text
        raise
    dt=info[pos:pos+2]
    print dt
    dt="%s %s" % tuple(dt)
# prolly use:
# datetime.strptime(date_string, format)
    dt=parse(dt)
    return dt

if __name__=='__main__':
    dvfile = 'pyohio.dv' 
    dt = get_timestamp(dvfile)
    print dt
    ts = time.mktime(dt.timetuple()) 
    print ts
    # os.utime(path, times) Set the access and modified 
    # os.utime(dvfile,(ts,ts))

