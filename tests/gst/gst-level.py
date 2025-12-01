#!/usr/bin/env python3

import optparse
import sys

import gi

# import pgi as gi

gi.require_version("Gst", "1.0")
from gi.repository import Gst, GLib

# init GObject & Co. before importing local classes
Gst.init([])


# Carl's abstract gst pipeline
class Abby:

    def __init__(self, options):

        # from parser.parse_args()
        # easy for this, but awkward to set otherwise
        self.options = options

        # hook to create whatever pipeline string you want
        pipeline = self.mk_pipeline()

        # build a pipeline object
        self.constuct_pipeline(pipeline)

        # wire it up to stuff we probably want
        self.setup_bus()
        self.connect_message()

        # hook to do the point of something
        self.my_name_is()

        # do it
        self.play_pipeline(pipeline)


    # __init
    def mk_pipeline(self):
        pipeline = "fakesrc ! fakesink"
        return pipeline

    def constuct_pipeline(self, pipeline):
        print("launch pipeline: " + pipeline)
        self.pipeline = Gst.parse_launch(pipeline)

    def setup_bus(self):

        bus = self.pipeline.get_bus()

        # Bind End-of-Stream-Signal on Source-Pipeline
        bus.add_signal_watch()
        bus.connect("message::eos", self.on_eos)
        bus.connect("message::error", self.on_error)

        self.bus = bus

    def connect_message(self):
        self.bus.connect("message", self._messageCb)

    def my_name_is(self):
        pass

    def play_pipeline(self, pipeline):
        print("playing")
        self.pipeline.set_state(Gst.State.PLAYING)

    # setup_bus
    def on_eos(self, bus, message):
        print("Received EOS-Signal")
        self.quit()

    def on_error(self, bus, message):
        print("Received Error-Signal")
        (error, debug) = message.parse_error()
        print(f"Error-Details: {error.code=}, {debug=}")
        self.quit()


    # connect_message
    def _messageCb(self, bus, message):

        t = message.type

        if t == Gst.MessageType.ELEMENT:
            self.process(t, bus, message)

        elif t == Gst.MessageType.ERROR:
            gerror, dbg_msg = message.parse_error()
            print(f"{gerror.message=}")
            print(f"{dbg_msg=}")
            self.quit()

        elif t == Gst.MessageType.EOS:
            print("EOS sys.quiting...")
            self.quit()

    # _messageCb if Gst.MessageType.ELEMENT
    def process(self, t, bus, message):
        pass


    def quit(self, exitcode=0):
        print("quit called, sys.exiting...")
        sys.exit(exitcode)


# class that does something:
# pass in options.audio_src
#  .process(levels)
class Level(Abby):

    def mk_pipeline(self):
        pipeline = f"{self.options.audio_src} ! level ! fakesink"
        return pipeline

    def my_name_is(self):

        print("setting up level...")

        level = self.pipeline.get_by_name("level0")
        level.set_property("interval", int(self.options.interval * Gst.SECOND))

        level.set_property("post-messages", True)


    def process(self, t, bus, message):

        if message.has_name("level"):

            s = message.get_structure()

            levs = {}
            for type in ("rms","peak","decay"):
                levs[type] = s.get_value(type)

            # levs["rms"] = s.get_value("rms")
            levs["delta"] = levs["decay"][0] - levs["rms"][0]

            if self.options.verbose:
                stream_time = s.get_value("stream-time")
                print(f"{stream_time/Gst.SECOND=:.4f}", end=" ")
                print(levs)

            if levs["rms"][0] < -55:
                return

            if levs["delta"] > self.options.threashold:
                self.triggered(s, message, levs)

            # if max(levs["rms"]) <= self.options.threashold:
            #    self.triggered(s, message, levs)


    # called when a level hits threashold
    def triggered(self, s, message, levs):
        print("triggered")

        print(levs)

        stream_time = s.get_value("stream-time")
        print(f"{stream_time/Gst.SECOND=:.2f}")

        # the start/end time of the window of time that triggered
        # I think stream-time is the end, so stream-time-interval is the start.
        print(f"{stream_time/Gst.SECOND - self.options.interval:.5f} - {stream_time/Gst.SECOND:.5f}")

        # self.quit(1)


def parse_args():
    parser = optparse.OptionParser()

    parser.add_option(
        "--audio-src",
        default="audiotestsrc freq=8820 num-buffers=500 ! audio/x-raw,channels=2",
        help="gst audio element",
    )

    parser.add_option(
        "--interval",
        type=float,
        default=1,
        help="buffer size in seconds",
    )

    parser.add_option(
        "-v",
        "--verbose",
        action="store_true",
        help="verbose",
    )

    parser.add_option(
        "--threashold",
        type=float,
        default=-8,
        help="if rms > threashold: exit",
    )

    options, args = parser.parse_args()

    return options, args


def main():

    options, args = parse_args()

    level = Level(options)

    mainloop = GLib.MainLoop()
    mainloop.run()


if __name__ == "__main__":
    main()
