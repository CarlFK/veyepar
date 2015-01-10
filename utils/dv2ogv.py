#!/usr/bin/python

# Adds the .dv files to the raw files table

import  os
import optparse
import subprocess

def dv2ogv(dv,ogv):
    # cmd="ffmpeg2theora --videoquality 1 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --keyint 256 --channels 1".split()
    cmd="ffmpeg2theora --videoquality 4 --audioquality 3 --audiobitrate 48 --speedlevel 2 --width 360 --keyint 256 ".split()
    cmd+=[ '-o', ogv, dv  ]
    print ' '.join(cmd)

    p=subprocess.Popen(cmd).wait()

def one_file(dv):
    # print dv,
    # print os.path.exists(dv)
    p,ext = os.path.splitext(dv)
    # print p
    ogv = "%s.%s" % (p,'ogv')
    if not os.path.exists(ogv):
        dv2ogv(dv,ogv)
    

def process(dv_dir):
    for dirpath, dirnames, filenames in os.walk(dv_dir,followlinks=True):
        d=dirpath[len(dv_dir)+1:]
        d=dirpath
        # print "checking...", dirpath, d, dirnames, filenames 
        filenames.sort()
        # for f in filenames[:-1]: ## skip the last one cuz it might be open
        for f in filenames: ## skip the last one cuz it might be open
            if f[-3:]=='.dv':
                one_file(os.path.join(d,f))

def parse_args():
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    return (options,args)

def main():
    options, args = parse_args()
    process(args[0])

if __name__ == "__main__":
    main()
