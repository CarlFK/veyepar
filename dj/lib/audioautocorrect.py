
#!/usr/bin/python3

#
# Copyright 2018 Meg Ford
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Library General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public
# License along with this library; if not, see <http://www.gnu.org/licenses/>.
#
# Author: Meg Ford <megford@gnome.org>
#
#

import argparse
import os
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstAudio', '1.0')
gi.require_version('Gtk', '3.0')
gi.require_version('GstPbutils', '1.0')
from gi.repository import Gst, GObject, Gtk, GstAudio, GstPbutils

GObject.threads_init()
Gst.init(None)

class AudioAutoCorrect:

    def on_end(self, bus, message):
        self.pipeline.set_state(Gst.State.NULL)
        bus.remove_signal_watch()
        Gtk.main_quit()

    def on_play_eos(self, bus, message):
        self.on_end(bus, message)

    def on_play_error(self, bus, message):
        self.on_end(bus, message)

    def valve_state(self, name, is_closed):
        valve = self.pipeline.get_by_name(name)

        if valve is None:
            print('Valve is broken')
            return

        if valve.get_property('drop') != is_closed:
            valve.set_property('drop', is_closed)


    def on_message(self, bus, message):
        struct = Gst.Message.get_structure(message)
        if struct.get_name() == 'level':
            array_val = struct.get_value('rms')
            # left is channel 0, right is channel 1
            # left is valve0, right is valve1
            l = False
            r = False
            l = array_val[0] < -55
            r = array_val[1] < -55
            print(array_val)

            # if (l == True and r == False):
            #     self.valve_state('valve1', False)
            #     self.valve_state('valve0', True)

            # elif l == True and r == True:
            #     # If they're both bad, choose the better one
            #     if array_val[0] < array_val[1]:
            #         valve_state('valve1', False)
            #         valve_state('valve0', True)

            #     else:
            #         valve_state('valve0', False)
            #         valve_state('valve1', True)

            # elif r == True and l == False:
            #     valve_state('valve0', False)
            #     valve_state('valve1', True)

            # else:
            #     self.valve_state('valve0', False)
            #     self.valve_state('valve1', False)

    def new_level_bin(self):
        bin = Gst.Bin()
        queue = Gst.ElementFactory.make('queue', 'queue')
        level = Gst.ElementFactory.make('level', 'level')
        fakesink = Gst.ElementFactory.make('pulsesink', 'consumer')
        level.set_property('post-messages', True)
        fakesink.set_property('async', False)
        bin.add(queue)
        bin.add(level)
        bin.add(fakesink)
        queue.link(level)
        level.link(fakesink)
        sink = queue.get_static_pad('sink')
        ghostpad = Gst.GhostPad.new('sink', sink)
        bin.add_pad(ghostpad)

        return bin


    def on_pad_added(self, element, pad):
        sink = None;
        pad_name = pad.get_name()

        if pad_name == 'src_0':
            sink = self.recorder0.get_static_pad('sink_0')
        elif pad_name == 'src_1':
            sink = self.recorder0.get_static_pad('sink_1')

        pad.link(sink)

    def on_dec_pad(self, dbin, pad):
        convert = self.pipeline.get_by_name('convert')
        dbin.link(convert)


    def new_recorder_bin(self, outfile):
        bin = Gst.Bin()
        interleave = Gst.ElementFactory.make('interleave', None)
        ebin = Gst.ElementFactory.make('encodebin', 'ebin');
        rec_caps = Gst.Caps.from_string('video/quicktime,variant=iso')
        container_profile = GstPbutils.EncodingContainerProfile.new('record', None, rec_caps, None)
        audio_caps = Gst.Caps.from_string('audio/mpeg,mpegversion=(int)4,channels=2')
        encoding_profile = GstPbutils.EncodingAudioProfile.new(audio_caps, None, None, 1)
        container_profile.add_profile(encoding_profile)
        ebinProfile = ebin.set_property('profile', container_profile)
        output = Gst.ElementFactory.make('filesink', 'output')
        output.set_property('location', outfile)
        output.set_property('async', False)
        srcpad = output.get_static_pad('src')
        bin.add(interleave)
        bin.add(ebin)
        bin.add(output)
        interleave.link(ebin)
        ebin.link(output)

        queue0 = Gst.ElementFactory.make('queue', 'l_queue')
        queue1 = Gst.ElementFactory.make('queue', 'r_queue')
        bin.add(queue0)
        bin.add(queue1)
        interleave.set_property('channel_positions', [
            GstAudio.AudioChannelPosition.FRONT_LEFT,
            GstAudio.AudioChannelPosition.FRONT_RIGHT
        ])
        sink0 = interleave.get_request_pad('sink_0')
        queue_sink0 = queue0.get_static_pad('sink')
        queue_src0 = queue0.get_static_pad('src')
        # valve0 = Gst.ElementFactory.make('valve', 'valve0')
        # valve0.set_property('drop', False)
        # bin.add(valve0)
        # valve_sink0 = valve0.get_static_pad('sink')
        # valve_src0 = valve0.get_static_pad('src')
        # valve_src0.link(sink0)
        # queue_src0.link(valve_sink0)
        queue_src0.link(sink0)
        ghostpad0 = Gst.GhostPad.new('sink_0', queue_sink0)
        sink1 = interleave.get_request_pad('sink_1')
        queue_sink1 = queue1.get_static_pad('sink')
        queue_src1 = queue1.get_static_pad('src')
        # valve1 = Gst.ElementFactory.make('valve', 'valve1')
        # valve1.set_property('drop', False)
        # bin.add(valve1)
        # valve_sink1 = valve1.get_static_pad('sink')
        # valve_src1 = valve1.get_static_pad('src')
        # queue_src1.link(valve_sink1)
        # valve_src1.link(sink1)
        queue_src1.link(sink0)
        ghostpad1 = Gst.GhostPad.new('sink_1', queue_sink1)
        bin.add_pad(ghostpad0)
        bin.add_pad(ghostpad1)

        return bin

    def pipeline(self, infile, outfile):
        self.pipeline = Gst.Pipeline.new('pipeline')
        play = Gst.ElementFactory.make('filesrc', 'play')
        play.set_property('location', infile)
        self.pipeline.add(play)
        decoder = Gst.ElementFactory.make('decodebin3', 'decoder')
        self.pipeline.add(decoder)
        convert = Gst.ElementFactory.make('audioconvert', 'convert')
        tee = Gst.ElementFactory.make('tee', None)
        level = self.new_level_bin()

        recorder = Gst.ElementFactory.make('queue', 'recording_queue')
        deinterleave = Gst.ElementFactory.make('deinterleave', 'splitter')

        self.recorder0 = self.new_recorder_bin(outfile)

        self.pipeline.add(convert)
        self.pipeline.add(tee)
        self.pipeline.add(level)
        self.pipeline.add(recorder)
        self.pipeline.add(deinterleave)
        self.pipeline.add(self.recorder0)

        if not play.link(decoder):
            print('filesrc and decoder elements not linked')

        if not convert.link(tee):
            print('convert and tee elements not linked')

        if not tee.link(level):
            print('tee and level elements not linked')

        decoder.connect('pad-added', self.on_dec_pad)
        self.pipeline.set_state(Gst.State.PLAYING)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()

        bus.connect('message::element', self.on_message)
        bus.connect('message::eos', self.on_play_eos)
        bus.connect('message::error', self.on_play_error)

        deinterleave.connect('pad-added', self.on_pad_added)

        if not tee.link(recorder):
            print('tee and recorder elements not linked')

        if not recorder.link(deinterleave):
            print('recorder and deinterleave elements not linked')

        Gtk.main()

class VideoAudioMerge:
    # gst-launch-1.0 filesrc location=recording.aac ! decodebin3 ! queue ! audioconvert ! "audio/x-raw,channels=2" ! faac ! mux. filesrc location=split.ts.mp4 ! decodebin3 ! videoconvert ! videoscale ! queue ! x264enc ! mpegtsmux name=mux ! filesink location=test.ts
    def pipeline(self, audiofile, videofile, outfile):
        launch_pipe = "filesrc name=filesrc ! decodebin3 ! queue ! audioconvert ! audio/x-raw,channels=2 ! faac ! mux. filesrc name=videofilesrc ! decodebin3 ! videoconvert ! videoscale ! queue ! x264enc ! mpegtsmux name=mux ! filesink name=filesink"

        self.pipeline = Gst.parse_launch(launch_pipe)

        # Set the filenames
        filesrc = self.pipeline.get_by_name('filesrc')
        filesrc.set_property('location', audiofile)
        video_filesrc = self.pipeline.get_by_name('videofilesrc')
        video_filesrc.set_property('location', videofile)
        filesink= self.pipeline.get_by_name('filesink')
        filesink.set_property('location', outfile)

        self.pipeline.set_state(Gst.State.PLAYING)
        bus = self.pipeline.get_bus()
        bus.add_signal_watch()

        bus.connect('message::eos', self.on_eos)
        bus.connect('message::error', self.on_error)
        Gtk.main()

    def on_end(self, bus, message):
        self.pipeline.set_state(Gst.State.NULL)
        bus.remove_signal_watch()
        Gtk.main_quit()

    def on_eos(self, bus, message):
        self.on_end(bus, message)

    def on_error(self, bus, message):
        self.on_end(bus, message)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=
    'Correct audio (ca), correct video (cv), combine audio and video (cb')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-ca', '--correct_audio', action='store_true')
    group.add_argument('-cb', '--combine', action='store_true')
    args = parser.parse_args()

    if args.correct_audio:
        audio = AudioAutoCorrect()
        audio.pipeline('13_05_53', 'recording.aac')

    if args.combine:
        merge = VideoAudioMerge()
        merge.pipeline('recording.aac', 'split.ts.mp4', 'out.ts')
