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
Gst.init(None)

class AudioPreviewer:

    count = 0
    interval = 1.0
    verbose = False
    filename = None

    def mk_pipe(self):
        
        uri = "file://%s" % (self.filename,)

        self.pipeline = Gst.parse_launch( "uridecodebin name=decode ! audioconvert ! level name=wavelevel post-messages=true ! fakesink qos=false name=faked" )

        decode = self.pipeline.get_by_name("decode")
        decode.set_property( 'uri', uri )

        wavelevel = self.pipeline.get_by_name( 'wavelevel' )
        wavelevel.set_property( 'interval', int(self.interval * Gst.SECOND))

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._messageCb)

        if self.verbose:
            print "playing..."
        self.pipeline.set_state(Gst.State.PLAYING)

        return

    def process(self, levs):
        # hook for more useful things.
        print self.count, levs
        self.count += 1
        return


    def _messageCb(self, bus, message):
        t = message.type

        if t == Gst.MessageType.ELEMENT \
              and message.has_name("level"):

            s = message.get_structure()
            try:
                levs={}
                for type in ("rms","peak","decay"):
                    levs[type] = s.get_value(type)

                if self.verbose:
                    print levs

                self.process(levs)

            except ValueError as e:
                print e

        elif t == Gst.MessageType.EOS:
            self.quit()

    def quit(self):
            self.pipeline.set_state(Gst.State.NULL)
            self.mainloop.quit()

# something useful

# pip install pypng numpy
# https://github.com/drj11/pypng

import png
import numpy 

class Make_png(AudioPreviewer):

    height = 50
    # don't care about anything under -40 (pretty quiet)
    threashold = -70
    channels = 2
    grid = None

    def setup(self):
        self.grid = numpy.zeros((self.height*self.channels,36000), dtype=numpy.uint8)
        self.mk_pipe()

    def process(self, levs):

        if self.channels == 2:
            # left rms 
            # map 0 to -40 to 0 to height
            l = int(max(levs['rms'][0],self.threashold) 
                    * (self.height-1)/self.threashold)
            for y in range(l,self.height):
                self.grid[y,self.count] = 127

            # left peak
            l = int(max(levs['peak'][0],self.threashold) 
                    * (self.height-1)/self.threashold)
            self.grid[l,self.count] = 255

            # right rms
            # map 0 to -70 to height to height * 2
            l = int(max(levs['rms'][1],self.threashold) 
                    * (self.height-1)/-self.threashold + 2 * self.height)
            for y in range(self.height,l):
                self.grid[y,self.count] = 127

            l = int(max(levs['peak'][1],self.threashold) 
                    * (self.height-1)/-self.threashold + 2 * self.height)
            self.grid[l,self.count] = 255

            self.grid[self.height,self.count] = 0

        else:

            for channel in range(self.channels):

                # map 0 to -40 to 0 to height
                l = int(max(levs['rms'][channel],self.threashold) 
                        * (self.height-1)/self.threashold)
                for y in range(l,self.height):
                    self.grid[y+channel*self.height,self.count] = 127

                # left peak
                l = int(max(levs['peak'][channel],self.threashold) 
                        * (self.height-1)/self.threashold)
                self.grid[l+channel*self.height,self.count] = 255

        self.count += 1

def lvlpng(file_name, png_name=None):

    p=Make_png()
    p.interval = options.interval
    p.height = options.height
    p.verbose = options.verbose
    p.channels = options.channels
    p.filename = file_name
    p.setup()

    p.mainloop = GLib.MainLoop()
    if options.verbose:
        print "looping..."
    p.mainloop.run()

    if png_name is None:
        png_name = os.path.splitext(filename)[0]+"_audio.png"

    if options.verbose:
        print png_name
    png.from_array([row[:p.count] for row in p.grid], 'L').save(png_name)

def many():
    for dirpath, dirnames, filenames in os.walk(
            options.indir, followlinks=True):
        d=dirpath[len(options.indir)+1:]
        for f in filenames:
            if f[-3:]=='.dv':
                rf_name = os.path.join(options.indir,d,f)
                png_name = os.path.join(options.outdir,d,
                        os.path.splitext(f)[0]+"_audio.png")
                lvlpng( rf_name, png_name )

def cklevels(file_name):
    p=AudioPreviewer()
    p.filename = filename
    p.mk_pipe()
    p.mainloop = GLib.MainLoop()
    p.mainloop.run()

    return 

def parse_args():
    parser = optparse.OptionParser()

    # parser.add_option('--start', type=int, default=0,
    #        help="start time", )
    # parser.add_option('--count', type=int, default=None,
    #        help="number of seconds", )
    parser.add_option('--channels', type=int, default=2,
            help="number of channels to render", )
    parser.add_option('--interval', type=float, default=1,
            help="buffer size in seconds", )
    parser.add_option('-v','--verbose', action="store_true",
            help="verbose", )

    parser.add_option('--height', type=int, default=50,
            help="height of image in pixels", )

    parser.add_option('--indir', 
            help="input dir", )
    parser.add_option('--outdir', 
            help="output dir", )

    options, args = parser.parse_args()
    return options,args

if __name__=='__main__':
    options,args = parse_args()

    if options.indir:
        many()
    else:
        if args:
            filename = args[0]
        else:
            # filename = "/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4"
            # filename = "/home/carl/temp/Manageable_Puppet_Infrastructure.webm"
            filename = "/home/carl/temp/15_57_39.ogv"
            filename = "/home/carl/src/veyepar/tests/165275__blouhond__surround-test-1khz-tone.wav"

        # cklevels(filename)
        lvlpng(filename)




