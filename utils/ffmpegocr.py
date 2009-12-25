#!/usr/bin/python

# ocrdv - reads frames from a .dv untill it finds a bunch of words

import subprocess
import optparse

import pyffmpeg
# http://code.google.com/p/pyffmpeg/issues/detail?id=9#c4

from cStringIO import StringIO
from csv import DictReader
from collections import defaultdict

titwords = None
dictionary = None

def ocrdv(dvfn):
    
    stream = pyffmpeg.VideoStream()
    stream.open(dvfn)
    frameno=0
    lastocr = ''
    done = False
    while not done:
  
        image = stream.GetFrameNo(frameno)

        # get PPM image from PIL image 
        buffer = StringIO()
        image.save(buffer,'PPM')
        img = buffer.getvalue()
        buffer.close()

        # ocr the image
        p = subprocess.Popen(['gocr', '-'], stdin=subprocess.PIPE, 
            stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        ocrtext, stderrdata = p.communicate(img)
        if stderrdata: print "ERR:", stderrdata
        if ocrtext: print "OUT:", ocrtext

        frameno+=30*15  # bump about 15 seconds

        print frameno

    return ocrtext,image

def parse_args():
    parser = optparse.OptionParser()
    return parser.parse_args()

if __name__=='__main__':
    options,args=parse_args();
    for dv in args:
        ocrdv(dv)


