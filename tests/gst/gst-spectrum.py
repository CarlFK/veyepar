#!/usr/bin/env python3

import optparse
import sys

import pgi as gi

gi.require_version('Gst', '1.0')
from gi.repository import Gst, GLib

# init GObject & Co. before importing local classes
Gst.init([])

class Spectrum:

    def __init__(self, options):

        pipeline = f"{options.audio_src} ! spectrum ! fakesink"
        print('setting up pipeline: ' + pipeline)

        self.pipeline = Gst.parse_launch(pipeline)

        bus = self.pipeline.get_bus()

        # Binding End-of-Stream-Signal on Source-Pipeline
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)

        bus.connect("message", self._messageCb)

        print('setting up spectrum...')
        spectrum = self.pipeline.get_by_name( 'spectrum0' )

        spectrum.set_property( 'bands', options.bands)
        spectrum.set_property( 'interval', int(options.interval * Gst.SECOND))

        spectrum.set_property( 'post-messages', True )

        print("playing")
        self.pipeline.set_state(Gst.State.PLAYING)

    def on_eos(self, bus, message):
        print('Received EOS-Signal')
        sys.exit()

    def on_error(self, bus, message):
        print('Received Error-Signal')
        (error, debug) = message.parse_error()
        print(f'Error-Details: {error.code=}, {debug=}')
        sys.exit(1)

    def _messageCb(self, bus, message):

        t = message.type

        if t == Gst.MessageType.ELEMENT \
              and message.has_name("spectrum"):

            s = message.get_structure()

            m = s.get_value("magnitude")

            self.process(m)

            print()

        elif t == Gst.MessageType.ERROR:
            gerror, dbg_msg = message.parse_error()
            print("Error : ", gerror.message)
            print("Debug details : ", dbg_msg)
            self.quit()

        elif t == Gst.MessageType.EOS:
            print("EOS sys.quiting...")
            self.quit()

    def quit(self):
        print("sys.exiting...")
        sys.exit()

    def process(self,m):
        for i in m:
            print(i)


def parse_args():
    parser = optparse.OptionParser()

    parser.add_option('--audio-src',
            default="audiotestsrc freq=8820 num-buffers=500",
            help="gst audio element")

    parser.add_option('--bands', type=int, default=20,
            help="Number of frequency bands")

    parser.add_option('--interval', type=float, default=1,
            help="buffer size in seconds", )

    options, args = parser.parse_args()
    return options,args


def main():

    options,args = parse_args()

    spectrum = Spectrum(options)

    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == '__main__':
    main()

