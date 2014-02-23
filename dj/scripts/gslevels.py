#!/usr/bin/python

# gslevel.py
# report audio levels
# to figure out what files are messed up

# http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good-plugins/html/gst-plugins-good-plugins-level.html

import optparse
import numpy
import os

from gi.repository import GObject, Gst, Gtk
from gi.repository import GLib
# GObject.threads_init()
Gst.init(None)


class AudioPreviewer:

    count = 0

    def __init__(self, filename ):
        
        uri = "file://%s" % (filename,)

        self.pipeline = Gst.parse_launch("uridecodebin name=decode uri=" + uri + " ! audioconvert ! level name=wavelevel interval=100000000 post-messages=true ! fakesink qos=false name=faked")
        # faked = self.pipeline.get_by_name("faked")
        # faked.props.sync = True

        # self.nSamples = self.bElement.get_parent().get_asset().get_duration() / 1000000000  ## 1,000,000,000 is 1 seconds
        self._level = self.pipeline.get_by_name("wavelevel")

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._messageCb)

        self.pipeline.set_state(Gst.State.PLAYING)


        return

    def process(self, levs):
        self.count += 1
        print self.count, levs
        return


    def _messageCb(self, bus, message):
        t = message.type

        # slightly different than
        # https://git.gnome.org/browse/pitivi/tree/pitivi/timeline/previewers.py#n867
        # if message.src == self._level:
        # >>> message.get_structure().get_name()=='level'

        if t == Gst.MessageType.ELEMENT \
              and message.has_name("level"):

            s = message.get_structure()

            try:
                levs = [[int(i) for i in s.get_value(type)]
                    for type in ("rms","peak","decay")]
                self.process(levs)

            except ValueError as e:
                print e


        elif t == Gst.MessageType.EOS:
            self.quit()

    def quit(self):
            print "quiting..."
            self.pipeline.set_state(Gst.State.NULL)
            self.mainloop.quit()


# pip install pypng numpy
# https://github.com/drj11/pypng

import png
import numpy 
from math import sin, pi, pow

class Make_png(AudioPreviewer):

    height = 50
    grid = numpy.zeros((height*2,36000), dtype=numpy.uint8)
    count = 0
    def process(self, levs):
        self.count += 1
        # [[-48, -48], [-48, -48], [-43, -12]]
        for i in [0]:
            # color = 127*i
            color = 255

            # math.pow( 10, val/20)
            # l =pow( 10, val/20 )
            # l = max(levs[i][0], -self.height-1)
            # r = max( levs[i][1], -self.height-1) + self.height
            # x = self.count/110.0 * -600 # self.height
            # print self.count, x
            l = max( levs[i][0], -(self.height-1)) + self.height 
            r = max( levs[i][1], -(self.height-1)) + self.height * 2
            self.grid[l, self.count] = color
            self.grid[r, self.count] = color

            for y1 in range(l+1,self.height):
                self.grid[y1,self.count] = 128
            for y1 in range(r+1,self.height*2):
                self.grid[y1, self.count] = 128


def lvlpng(file_name):

    p=Make_png(file_name)
    p.mainloop = GLib.MainLoop()
    p.mainloop.run()

    print "p.count", p.count
    print "len(p.grid[0])", len(p.grid[0])
    
    # np.resape( p.grid, (p.count,-1
    # png.from_array(p.grid, 'L').save("test.png")
    pngname = os.path.splitext(filename)[0]+"_audio.png"
    png.from_array([row[:p.count] for row in p.grid], 'L').save(pngname)

def cklevels(file_name):
    p=AudioPreviewer(file_name)
    p.mainloop = GLib.MainLoop()
    p.mainloop.run()

    return 

def parse_args():
    parser = optparse.OptionParser()

    parser.add_option('--start', type=int, default=0,
            help="start time", )
    parser.add_option('--count', type=int, default=None,
            help="number of seconds", )

    options, args = parser.parse_args()
    return options,args

if __name__=='__main__':
    options,args = parse_args()
    # filename = "/home/carl/src/veyepar/dj/scripts/foo.dv"
    # filename = "/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4"
    # filename = "/home/carl/temp/Manageable_Puppet_Infrastructure.webm"
    # filename = "/home/carl/temp/15_57_39.ogv"

    filename = args[0]
    
    # cklevels(uri)
    lvlpng(filename)


