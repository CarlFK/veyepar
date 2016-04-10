#!/usr/bin/python

# cklevel.py
# check level - look for audio
# to figure out what files are messed up
# (now just tring to play a file - first pygst code ever)

import optparse

import pygst
pygst.require("0.10")
import gst
import pygtk
import gtk
import gobject

import code

class Main:

    def next_file(self):
        filename=self.files.pop()
        print(filename)
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

# convert from this to that?!!
        convert = gst.element_factory_make("audioconvert", "convert")
        pipeline.add(convert)
# store to attribute so OnDynamicPad() can get it
        self.convert = convert

# monitor audio level
        level = gst.element_factory_make("level", "level")
        level.set_property("message", True)
        pipeline.add(level)
        convert.link(level)
        
# send it to alsa        
        alsa = gst.element_factory_make("alsasink", "alsa")
        pipeline.add(alsa)
        level.link(alsa)

# keep refernce to pipleline so it doesn't get destroyed 
        self.pipeline=pipeline
        pipeline.set_state(gst.STATE_PLAYING)

        bus = pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self.on_message)


    def OnDynamicPad(self, dbin, pad, islast):
        print("OnDynamicPad Called!")
        # print pad.get_caps()[0].get_name()
        if pad.get_caps()[0].get_name().startswith('audio'):
            pad.link(self.convert.get_pad("sink"))
        # code.interact(local=locals())

    def on_message(self, bus, message):
        t = message.type
        if t == gst.MESSAGE_ELEMENT \
                and message.structure.get_name()=='level':

            levs = [message.structure[type] for type in ("rms","peak","decay")]
            levs = [int(l[0]) for l in levs]
            lev = levs[1]
            # rms = 10.0**(lev / 20.0)
            # print lev, "*"* int(-lev/2)
            if self.min is None or lev < self.min:
                self.min = lev
            if self.max is None or lev > self.max:
                self.max = lev
            dif= self.max-self.min
            print(levs, self.min, self.max, dif)
            if levs[1]>-10:
                pass
                # self.next_file()

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
    p=Main(args)
    gtk.main()
