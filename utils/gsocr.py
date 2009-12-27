#!/usr/bin/python

# gsocr.py
# uses gstreamer to send frames to gocr

import subprocess
import optparse

import pygtk
pygtk.require ("2.0")
import gobject
gobject.threads_init ()
import pygst
pygst.require ("0.10")
import gst

import gtk
 
def Dictionary():
    dictionary = [w for w in open('dictionary.txt').read().split() if len(w)>3]
    return dictionary

def one_frame( sink,buffer,pad, it):
    # print len(buffer)
    if len(buffer) == 15:
        it.p = subprocess.Popen(['gocr', '-'], stdin=subprocess.PIPE, 
          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        it.p.stdin.write(buffer)  
        it.f=open('foo.pnm','wb')
        it.f.write(buffer)  

        it.skip=False ## don't seek yet, need to get the 2nd part below

    else:
        it.f.write(buffer)
        it.f.close()

        ocrtext, stderrdata = it.p.communicate(buffer)

        if it.last_ocr != ocrtext:
            it.last_ocr=ocrtext
            words = [w for w in ocrtext.split() if w.upper() in it.dictionary]
            print ocrtext.__repr__()[:70]
            # print "last", it.last_words
            # print "cur", words
            if it.last_words != words:
                it.last_words = words
                print words[:10]

        it.skip=True ## flag to seek

    return   
    
def skip_forward(it):

    if it.skip:
        # print "in skip_forward..."
        it.skip=False
        pos_int = it.pipeline.query_position(it.time_format, None)[0]
        # print "starting at", pos_int
        seek_ns = pos_int + (10 * 1000000000)
        it.pipeline.seek_simple(it.time_format, gst.SEEK_FLAG_FLUSH, seek_ns)

    return True

class Main:

    def __init__(self, filename):
        
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
        pipeline.set_state(gst.STATE_PLAYING)

        self.time_format = gst.Format(gst.FORMAT_TIME)

        elements=list(pipeline.elements())
        elements.reverse()
        for e in elements:
            print e.get_factory().get_name(),
        print

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        # bus.connect("message", self.on_message)

        self.skip = False
        self.last_ocr=''
        self.last_words=[]
        self.dictionary=Dictionary()

    def OnDynamicPad(self, dbin, pad, islast):
        print "OnDynamicPad Called!"
        print pad.get_caps()[0].get_name()
        if pad.get_caps()[0].get_name().startswith('video'):
            pad.link(self.ffmpegcolorspace.get_pad("sink"))
            # pad.link(self.pnmenc.get_pad("sink"))

    def on_message(self, bus, message):
        print message
        t = message.type
        print t
        if t == gst.MESSAGE_ELEMENT:
            pass
        elif t == gst.MESSAGE_EOS:
            # self.player.set_state(gst.STATE_NULL)
            self.next_file()

def parse_args():
    parser = optparse.OptionParser()
    options, args = parser.parse_args()
    return options,args

if __name__=='__main__':
    options,args = parse_args()
    gobject.threads_init()
    if not args: args=['foo.dv']
    p=Main(args[0])
    gobject.idle_add( skip_forward, p, priority=gobject.PRIORITY_HIGH )
    gtk.main()
