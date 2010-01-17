#!/usr/bin/python

# gsocr.py
# uses gstreamer to send frames to gocr

import subprocess
import os
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

dict_loc =  pkg_resources.resource_filename('gsocr', 'static/dictionary.txt')
dictionary = [w.upper() for w in open(dict_loc).read().split() if len(w)>3]

def ckocr(it,ocrtext):
    ret = False
    if it.last_ocr != ocrtext:
        it.last_ocr=ocrtext
        words = [w for w in ocrtext.split() if w.upper() in dictionary]
        print ocrtext.__repr__()[:70]
        if it.words is None or len(it.words) < len(words):
            it.words = words
            print words
            ret = True

    return ret

def one_frame( sink,buffer,pad, it):
    # print len(buffer)
    if len(buffer) == 15:
        it.buffer = buffer

    else:

        p = subprocess.Popen(['gocr', '-', '-d', '0', '-a', '95'], 
          stdin=subprocess.PIPE, 
          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        p.stdin.write(it.buffer)  
        ocrtext, stderrdata = p.communicate(buffer)

        if ckocr(it,ocrtext):
            it.frame = it.pipeline.query_position(it.time_format, None)[0]
       
            # write image out to a file
            f=open(it.imgname,'wb')
            f.write(it.buffer)  
            f.write(buffer)
            f.close()

        gobject.idle_add( skip_forward, it, priority=gobject.PRIORITY_HIGH )

    return   
    
def skip_forward(it):

    pos_int = it.pipeline.query_position(it.time_format, None)[0]
    seek_ns = pos_int + (2000 * 1000000000)
    it.pipeline.seek_simple(it.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)

    return False

class Main:

    def __init__(self, filename):

        self.last_ocr=''
        self.words=None
        self.frame=0
        self.imgname="%s.pnm" % os.path.splitext(filename)[0] 

        filename
        
        self.base_name=os.path.splitext(filename)[0]
        print self.base_name

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

        elements=list(pipeline.elements())
        elements.reverse()
        for e in elements:
            print e.get_factory().get_name(),
        print

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

        pipeline.set_state(gst.STATE_PLAYING)

    def OnDynamicPad(self, dbin, pad, islast):
        print "OnDynamicPad Called!"
        print pad.get_caps()[0].get_name()
        if pad.get_caps()[0].get_name().startswith('video'):
            pad.link(self.ffmpegcolorspace.get_pad("sink"))

    def on_message(self, bus, message):
        # print message
        t = message.type
        # print t
        # if t == gst.MESSAGE_ELEMENT:
        #     pass
        if t == gst.MESSAGE_EOS:
            # self.player.set_state(gst.STATE_NULL)
            print self.frame, self.words
            gtk.main_quit()

def parse_args():
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    return options,args

if __name__=='__main__':
    options,args = parse_args()
    gobject.threads_init()
    if not args: args=['foo.dv']
    p=Main(args[0])
    gtk.main()
