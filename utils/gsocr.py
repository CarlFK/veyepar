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
 
def one_frame(sink,buffer,pad,it):
    if len(buffer) == 15:
        it.p = subprocess.Popen(['gocr', '-'], stdin=subprocess.PIPE, 
          stdout=subprocess.PIPE,stderr=subprocess.PIPE)
        it.p.stdin.write(buffer)  
        it.f=open('foo.pnm','wb')
        it.f.write(buffer)  
    else:
        it.f.write(buffer)
        it.f.close()

        ocrtext, stderrdata = it.p.communicate(buffer)
        print ocrtext

        # sink.set_state(gst.STATE_NULL )

    return   
    
class Main:

    def next_file(self):
        filename=self.files.pop()
        print filename
        self.min,self.max = None,None
        self.pipeline.set_state(gst.STATE_NULL)
        self.filesrc.set_property("location", filename)
        self.pipeline.set_state(gst.STATE_PLAYING)

    def __init__(self, files):
        
        self.files = files

        pipeline = gst.Pipeline("mypipeline")
        self.pipeline=pipeline

# source: file
        filesrc = gst.element_factory_make("filesrc", "audio")
        self.filesrc = filesrc
        self.next_file()
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
        sink.connect('handoff',one_frame,self)
        pipeline.add(sink)
        pnmenc.link(sink)

# Output images as GdkPixbuf objects in bus messages
        # gdkpixbufsink = gst.element_factory_make("gdkpixbufsink", "gdkpixbufsink")
        # pipeline.add(gdkpixbufsink)
        # ffmpegcolorspace.link(gdkpixbufsink)

# keep refernce to pipleline so it doesn't get destroyed 
        self.pipeline=pipeline
        pipeline.set_state(gst.STATE_PLAYING)

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)

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
        if t == gst.MESSAGE_ELEMENT \
                and message.structure.get_name()=='pixbuf':
            pixbuf=message.structure['pixbuf']
            lst=[]
            pixbuf.save_to_callback(
                lambda b,l: l.append(b), 'bmp', user_data=lst)
            img=''.join(lst)
            open('foo.bmp','wb').write(img)


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
    p=Main(args)
    gtk.main()
