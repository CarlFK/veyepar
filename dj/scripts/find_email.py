#!/usr/bin/python

# find_email.py
# uses gstreamer to send frames to gocr and look for email addresses

"""
every 10 sec, ocr
if @, append
maybe do better later
"""

import subprocess
import os
from cStringIO import StringIO
import ImageFile

import optparse

import pygtk
pygtk.require ("2.0")
import gobject
gobject.threads_init ()
import pygst
pygst.require ("0.10")
import gst

import gtk
 
import pkg_resources

"""
Huh, I wonder why one_frame and skip_forward are functions 
and not methods of class Main: ?
My guess is needing the object ref at the end of the parameters.
"""

def one_frame( sink,buffer,pad, it):
    # gstreamer sends frames in 2 parts: header + image
    # the header is 15 bytes, save it for when the 2nd part comes in.
  
    if len(buffer) == 15:
        it.buffer = buffer

    else:
        # 2nd part has arrived in buffer, the first is in it.buffer.
        
        # p = subprocess.Popen(['gocr', '-', '-d', '0', '-a', '95'], 
        f = open('/tmp/image.pnm','w')
        f.write(it.buffer)
        f.write(buffer)
        f.close()
        p = subprocess.Popen(it.ocr_cmd)
        x = p.wait()
        ocrtext = open('/tmp/text.txt').read()
        
        """
        p = subprocess.Popen(it.gocr_cmd,
          stdin=subprocess.PIPE, 
          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        # send the 2 parts to gocr:
        # 1. write 15 byte header
        p.stdin.write(it.buffer)  
        # 2. write rest of image and get return values
        ocrtext, stderrdata = p.communicate(buffer)
        """

        if it.last_ocr != ocrtext:
            it.last_ocr=ocrtext

            if "@" in ocrtext:
                it.words += ocrtext
                it.frame = it.pipeline.query_position(it.time_format, None)[0]
       
            """
            # convert it to a png (for firefox and uploading as thumb)
            p = subprocess.Popen(
                ['convert', '-', "png:"+it.base_name+'.png'],
                stdin=subprocess.PIPE, 
                stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            p.stdin.write(it.buffer)  
            sout, serr = p.communicate(buffer)
            if it.debug: print sout, serr
            """

        gobject.idle_add( skip_forward, it, priority=gobject.PRIORITY_HIGH )
        
        # it.seek_sec = it.seek_sec*1.1

    return   
    
def skip_forward(it):

    pos_int = it.pipeline.query_position(it.time_format, None)[0]
    seek_ns = pos_int + (it.seek_sec * 1000000000)
    it.pipeline.seek_simple(it.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)

    return False

class Main:

    def __init__(self, filename):

        self.debug=True
        self.last_ocr=''

        self.words=''
        self.frame=0
        self.seek_sec = 30
        # self.gocr_cmd = ['gocr', '-', '-d', '0', '-a', '95'] 
        self.ocr_cmd = ['tesseract', '/tmp/image.pnm', '/tmp/text'] 

        self.base_name=os.path.splitext(filename)[0]
        if self.debug: print self.base_name

        pipeline = gst.Pipeline("mypipeline")
        self.pipeline=pipeline

# source: file
        filesrc = gst.element_factory_make("filesrc", "audio")
        self.filesrc = filesrc
        self.filesrc.set_property("location", filename)
        pipeline.add(filesrc)

# decoder
        decode = gst.element_factory_make("decodebin", "decode")
        decode.connect("new-decoded-pad", self.OnDynamicPad)
        pipeline.add(decode)
        filesrc.link(decode)

        ffmpegcolorspace = gst.element_factory_make("ffmpegcolorspace", "ffmpegcolorspace")
        pipeline.add(ffmpegcolorspace)
        self.ffmpegcolorspace=ffmpegcolorspace

        pnmenc = gst.element_factory_make("pnmenc", "pnmenc")
        pnmenc.set_property('ascii',True)
        pipeline.add(pnmenc)
        self.pnmenc = pnmenc
        ffmpegcolorspace.link(pnmenc)
        
        sink = gst.element_factory_make("fakesink", "sink")
        sink.set_property('signal-handoffs',True)
        sink.connect('handoff', one_frame, self )
        pipeline.add(sink)
        pnmenc.link(sink)

# keep refernce to pipleline so it doesn't get destroyed 
        self.pipeline=pipeline

        self.time_format = gst.Format(gst.FORMAT_TIME)

        if self.debug: 
            # print the pipeline 
            elements=list(pipeline.elements())
            elements.reverse()
            print "pipeline elements:",
            for e in elements:
                print e.get_factory().get_name(),
            print

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        pipeline.set_state(gst.STATE_PLAYING)

    def OnDynamicPad(self, dbin, pad, islast):
        # print "OnDynamicPad Called!"
        # print pad.get_caps()[0].get_name()
        if pad.get_caps()[0].get_name().startswith('video'):
            pad.link(self.ffmpegcolorspace.get_pad("sink"))

    def on_message(self, bus, message):
        # print message
        t = message.type
        # print t
        # if t == gst.MESSAGE_ELEMENT:
        #     pass
        if t == gst.MESSAGE_ERROR:
            print "error:", message, dir(message), message.parse_error()
            self.pipeline.set_state(gst.STATE_NULL)  
            gtk.main_quit()
        if t == gst.MESSAGE_EOS:
            if self.debug: print self.frame, self.words
            self.pipeline.set_state(gst.STATE_NULL)  
            gtk.main_quit()

def parse_args():
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    return options,args

if __name__=='__main__':
    options,args = parse_args()
    gobject.threads_init()
    # if not args: args=['00:00:00.dv']
    if not args: args=['/home/juser/Videos/veyepar/freegeek_chicago/sfd_2013/dv/freegeekchi/2013-09-21/12_46_06.dv']
    p=Main(args[0])
    p.debug=True
    gtk.main()
