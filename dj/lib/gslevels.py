#!/usr/bin/python

# gslevels.py
# report audio levels
# to figure out what files are messed up

# http://gstreamer.freedesktop.org/data/doc/gstreamer/head/gst-plugins-good-plugins/html/gst-plugins-good-plugins-level.html

# gst-launch-1.0 uridecodebin name=decode uri="file://$PWD/SC1ATK103.mov" ! audioconvert ! level name=wavelevel post-messages=true ! fakesink --messages

# gst-launch-1.0 filesrc location="SC1ATK105.mov" ! qtdemux ! audioconvert ! level name=wavelevel post-messages=true ! fakesink --messages

import optparse
import numpy
import os

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib
Gst.init(None)

from mk_mlt import set_text, set_attrib

class AudioPreviewer:

    count = 0
    interval = 1.0  ## buffer size in seconds
    verbose = False
    # uri = None
    location = None

    def mk_pipe(self):

        # self.pipeline = Gst.parse_launch( "uridecodebin name=decode ! audioconvert ! level name=wavelevel ! fakesink name=faked" )
        # self.pipeline = Gst.parse_launch( "filesrc name=filesrc ! qtdemux ! audioconvert ! level name=wavelevel ! fakesink")
        # "filesrc name=filesrc ! decodebin3 ! audioconvert ! level name=wavelevel ! fakesink"
        # "uridecodebin3 name=decode ! audioconvert ! level name=wavelevel ! fakesink"
        self.pipeline = Gst.parse_launch(
            "filesrc name=filesrc ! decodebin3 ! audioconvert ! level name=wavelevel ! fakesink"
            )

        """
        # removed so I can use decodebin3
        # because: https://bugzilla.gnome.org/show_bug.cgi?id=770498
        self.uri = self.location
        if self.uri.startswith('/'):
            self.uri = "file://" + self.uri
        decode = self.pipeline.get_by_name("decode")
        decode.set_property( 'uri', self.uri )
        """

        filesrc = self.pipeline.get_by_name("filesrc")
        filesrc.set_property( 'location', self.location )

        wavelevel = self.pipeline.get_by_name( 'wavelevel' )
        wavelevel.set_property( 'interval', int(self.interval * Gst.SECOND))
        wavelevel.set_property( 'post-messages', True )

        bus = self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.connect("message", self._messageCb)

        return

    def process(self, levs):
        # hook for more useful things.
        print(self.count, levs)
        self.count += 1
        return


    def _messageCb(self, bus, message):

        if message is None:
            print(("_messageCb called with bus:{} message:{}".format(
                bus, message)))
            import code; code.interact(local=locals())

        t = message.type

        if self.verbose:
            print(( "verbose: _messageCb called with bus:{} message:{}".format(bus, message)))
            print(( "type:", t ))
            # import code; code.interact(local=locals())

        if t == Gst.MessageType.ELEMENT \
              and message.has_name("level"):

            s = message.get_structure()
            try:
                levs={}
                for type in ("rms","peak","decay"):
                    levs[type] = s.get_value(type)

                if self.verbose:
                    print(levs)

                self.process(levs)

            except ValueError as e:
                print("Error: {}".format(e))

        elif t == Gst.MessageType.ERROR:
            gerror, dbg_msg = message.parse_error()
            print("Error : ", gerror.message)
            print("Debug details : ", dbg_msg)
            self.quit()

        elif t == Gst.MessageType.EOS:
            self.quit()

    def start(self):
        if self.verbose:
            print("playing...")
        self.pipeline.set_state(Gst.State.PLAYING)
        self.mainloop = GLib.MainLoop()
        if self.verbose:
            print("looping...")
        self.mainloop.run()

    def quit(self):
        self.pipeline.set_state(Gst.State.NULL)
        self.mainloop.quit()

# something useful

# pip install pypng numpy
# https://github.com/drj11/pypng

import png
import numpy
import urllib.parse

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

        # 0 out positive levels
        # above 0 is cliping, don't care how much
        # can't put data outside the png canvas
        for type in ("rms","peak","decay"):
            levs[type] = [min(lev,0) for lev in levs[type]]

        # tick mark every minute (I think)
        tick = 1 if self.count % 60 == 59 else 0
        # bigger one every 10
        tick = 3 if self.count % 600 == 599 else 0
        if self.channels == 2:
            # left rms
            # map 0 to -40 to 0 to height
            l = int(max(levs['rms'][0],self.threashold)
                    * (self.height-1)/self.threashold)
            for y in range(l,self.height-tick):
                self.grid[y,self.count] = 127

            # left peak
            l = int(max(levs['peak'][0],self.threashold)
                    * (self.height-1)/self.threashold)
            self.grid[l,self.count] = 255

            # right rms
            # map 0 to -70 to height to height * 2
            l = int(max(levs['rms'][1],self.threashold)
                    * (self.height-1)/-self.threashold + 2 * self.height)
            for y in range(self.height+tick,l):
                self.grid[y,self.count] = 127

            l = int(max(levs['peak'][1],self.threashold)
                    * (self.height+1)/-self.threashold + 2 * self.height-2)
            self.grid[l,self.count] = 255

            self.grid[self.height,self.count] = 0

        else:

            for channel in range(self.channels):

                # map 0 to -40 to 0 to height
                l = int(max(levs['rms'][channel],self.threashold)
                        * (self.height-1)/self.threashold)
                for y in range(l,self.height-tick):
                    self.grid[y+channel*self.height,self.count] = 127

                # left peak
                l = int(max(levs['peak'][channel],self.threashold)
                        * (self.height-1)/self.threashold)
                self.grid[l+channel*self.height,self.count] = 255

        self.count += 1

    def mk_png(self, png_name):
        if self.count:
            png.from_array(
                    [row[:self.count] for row in self.grid], 'L').save(png_name)
        else:
            # no audio data, make a 1x1 png
            png.from_array([(0,0)], 'L').save(png_name)

        return True


import xml.etree.ElementTree
import copy

class Make_mlt_fix_1(AudioPreviewer):

    height = 50
    # don't care about anything under -40 (pretty quiet)
    threashold = -70
    channels = 2
    grid = None

    tree = None
    nodes = {}

    def setup(self):
        self.grid = numpy.zeros((self.height*self.channels,36000), dtype=numpy.uint8)
        self.mk_pipe()

        tree = xml.etree.ElementTree.parse('one_ts.mlt')

        node_names=[
                'producer0',  # 1 segment
                'channelcopy', # channel copy
                'playlist0', # list of segments
                'pi', # playlist item
                ]
        nodes={}
        for id in node_names:
            node = tree.find(".//*[@id='{}']".format(id))
            # print(id,node)
            # assert id is not None
            nodes[id] = node

        # remove all placeholder nodes
        mlt = tree.find('.')

        play_list = tree.find("./playlist[@id='playlist0']")
        for pe in play_list.findall("./entry[@producer]"):
            producer = pe.get('producer')
            producer_node = tree.find("./producer[@id='{}']".format(producer))
            # print( producer )
            play_list.remove(pe)
            mlt.remove(producer_node)

        self.tree = tree
        self.nodes = nodes


    def process(self, levs):

        # (rms,peek),bad
        out = [ [[None,None],None], [[None,None],None] ]

        # 0 out positive levels (above 0 is cliping, don't care how much)
        for type in ("rms","peak","decay"):
            levs[type] = [min(lev,0) for lev in levs[type]]

        # tick mark every minute (I think)
        tick = 2 if self.count % 600 == 599 else 0
        # left rms
        # map 0 to -40 to 0 to height
        l = int(max(levs['rms'][0],self.threashold)
                * (self.height-1)/self.threashold)

        bad1 = l > 40 # 45 was pretty good, but looks like it missed some
        bad = levs['rms'][0] < -55
        if self.verbose:
            if bad1 != bad: print(l, levs['rms'][0])

        color = 127 if bad else 192

        for y in range(l,self.height-tick):
            self.grid[y,self.count] = color
        out[0][0][0]=levs['rms'][0]

        # left peak
        l = int(max(levs['peak'][0],self.threashold)
                * (self.height-1)/self.threashold)
        self.grid[l,self.count] = 255
        out[0][0][1]=levs['peak'][0]
        out[0][1]='bad' if bad else ''

        # right rms
        # map 0 to -70 to height to height * 2
        l = int(max(levs['rms'][1],self.threashold)
                * (self.height-1)/-self.threashold + 2 * self.height)
        for y in range(self.height+tick,l):
            self.grid[y,self.count] = color
        out[1][0][0]=l

        l = int(max(levs['peak'][1],self.threashold)
                * (self.height+1)/-self.threashold + 2 * self.height-2)
        self.grid[l,self.count] = 255

        out[1][0][1]=l
        out[1][1]='bad' if bad else ''

        self.grid[self.height,self.count] = 0

        if self.verbose:
            print(out)


        # add a clip to the mlt tree

        playlist = self.tree.find("./playlist[@id='playlist0']")
        node_id = "ti_{}".format(self.count)

        tl = copy.deepcopy( self.nodes['pi'] )
        tl.set("producer", node_id)
        set_attrib(tl, "in", self.count)
        set_attrib(tl, "out", self.count+1)
        playlist.insert(self.count,tl)

        ti = copy.deepcopy( self.nodes['producer0'] )
        ti.set("id", node_id)
        set_attrib(ti, "in")
        set_attrib(ti, "out")
        set_text(ti,'length')
        set_text(ti,'resource',self.location)

        # apply the filters to the cut

        channelcopy = copy.deepcopy( self.nodes['channelcopy'] )
        if bad:
            set_text(channelcopy,'from' , '1')
            set_text(channelcopy,'to' , '0')
        else:
            set_text(channelcopy,'from' , '0')
            set_text(channelcopy,'to' , '1')

        ti.insert(0,channelcopy)

        mlt = self.tree.find('.')
        mlt.insert(1,ti)

        self.count += 1


    def mk_png(self, png_name):
        if self.count:
            png.from_array(
                    [row[:self.count] for row in self.grid], 'L').save(png_name)
        else:
            # no audio data, make a 1x1 png
            png.from_array([(0,0)], 'L').save(png_name)

        return True



def lvlpng(filename, png_name=None):
    """
    given:
      uri - input uri
      png_name - output path and filename
       (defaults to input.wav.png,
         munged if input is http)
    """

    p=Make_png()
    # p=Make_mlt_fix_1()
    p.interval = options.interval
    p.height = options.height
    p.verbose = options.verbose
    p.channels = options.channels
    p.location = filename
    p.setup()
    p.start()
    p.tree.write('test.mlt')

    if png_name is None:
        pathname = filename
        """
        o = urlparse.urlparse(uri)
        if o.scheme=="file":
            pathname = o.path
        else:
            # drops output in local dir
            # use png_name parameter to make it go somewhere else
            pathname = o.path.split('/')[-1]
        png_name = os.path.splitext(pathname)[0]+".wav.png"
        """
        png_name = pathname+".wav.png"

    p.mk_png(png_name)
    print(png_name)


def many(indir, outdir):
    """
    given:
      options.indir - dir to recurse from looking for .dv files
      options.outdir - dir to put results in (keeps the same tree found)
    uses lvlpng() to create output files.
    """

    if outdir is None: outdir = indir

    for dirpath, dirnames, filenames in os.walk( indir, followlinks=True):
        d=dirpath[len(options.indir)+1:]
        for f in filenames:
            if os.path.splitext(f)[1] in ['.mov','.ts', '.dv']:
                rf_name = os.path.join(options.indir,d,f)
                png_name = os.path.join(outdir,d,f+".wav.png")
                if options.verbose:
                    print(rf_name)
                    print(png_name)
                if not os.path.exists(png_name):
                    lvlpng( rf_name, png_name )


def cklevels(filename):
    """
    tests the gstreamer functionality:
      report levels from an input file.
    """
    p=AudioPreviewer()
    p.location = filename
    p.mk_pipe()
    p.start()

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
    parser.add_option('--test', action="store_true",
            help="test the gstreamer bits", )

    parser.add_option('--height', type=int, default=50,
            help="height of image in pixels", )

    parser.add_option('--indir',
            help="input dir", )
    parser.add_option('--outdir',
            help="output dir", )

    options, args = parser.parse_args()
    return options,args


def main():

    """
    filenames = [
   # "/home/carl/Videos/veyepar/test_client/test_show/mp4/Test_Episode.mp4",
   # "/home/carl/temp/Manageable_Puppet_Infrastructure.webm",
   # "/home/carl/temp/15_57_39.ogv",
   #"/home/carl/src/veyepar/tests/165275__blouhond__surround-test-1khz-tone.wav",
    # "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Swang_102/2015-11-14/cam/10_51_03/00002.MTS",
    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Stowe_Hall/2015-11-14/graphics swang 11:14/Clip1GTK19.mov",
    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Stowe_Hall/2015-11-14/video swang 11:14/Clip1ATK1.mov",
    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Collins_Auditorium/2015-11-14/Saturday Morning Camera/SC1ATK103.mov",
    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Collins_Auditorium/2015-11-14/Saturday Morning GFX/Clip1ATK653.mov",
    ]

    for filename in filenames:
        if options.test:
            cklevels(filename)
        else:
            lvlpng(filename)

    return
    """

    if options.indir:
        many(options.indir, options.outdir)
    else:
        if args:
            uris = args
        else:
            uris = [ "file://%s" % (filename,) for filename in [
                      ]]

        for uri in uris:
            if options.test:
                cklevels(uri)
            else:
                lvlpng(uri)

if __name__=='__main__':
    options,args = parse_args()
    main()
