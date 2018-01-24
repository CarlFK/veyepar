#!/usr/bin/python

"""
tsdv.py - timestamp dv
sets start/end times of dv files

Gets start from one of:
the file name (assumes yy_mm_dd/hh_mm_ss.dv format)
the file system time stamp,
the first frame of the dv

duration (in seconds) based on file size / BBF*FPS
last frame

"""

import os
import datetime
from fnmatch import fnmatch

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

import tsraw

class ts_rf(process):

    def one_rf(self, rf):

        pathname=os.path.join(self.show_dir, 'dv',
                rf.location.slug, rf.filename)

        if self.options.verbose: print(pathname)

        # print( "tsraw.get_start", (pathname, self.options.time_source ) )
        start = tsraw.get_start(pathname, self.options.time_source )

        """
        if offset is not None:
            start += datetime.timedelta(seconds=offset)
        """

        """
        # when did this start working?
        if os.path.splitext(rf.filename)[1] in [ '.ts' ]:
            seconds = 1800
        else:
            seconds = tsraw.get_duration(pathname)
        """
        if not os.path.exists(pathname):
            print('missing file: {}'.format(pathname))
            if self.options.delete_unknown:
                rf.delete()
            return
        seconds = tsraw.get_duration(pathname)

        print(( pathname, start, seconds ))
        rf.start = start

        hms = seconds//3600, (seconds%3600)//60, seconds%60
        duration = "%02d:%02d:%02d" % hms

        rf.duration = duration

        rf.save()

    def one_loc(self, show, location):
        print(show,location)
        for rf in Raw_File.objects.filter(show=show, location=location):
            if self.options.verbose:
                print(1, rf.filename)
                print(1, self.args)

            if self.args:
                print(2, rf.filename)
                print(2, self.args)
                if not any(
                    fnmatch(rf.filename,mask) for mask in self.args):
                    # only process files listed on the command line
                    continue

            if self.options.ext:
                if not rf.filename.endswith(self.options.ext):
                    # skip
                    continue

            if self.options.subs:
                # subs holds a bit of the dirs we want,
                # like graphics,video,Camera,GFX
                if not self.options.subs in rf.filename:
                    continue

            # offset = self.options.offset_seconds

            if not rf.start or self.options.force:
                # self.one_rf(rf, offset )
                self.one_rf(rf )

    def work(self):
        """
        find and process show
        """
        if self.options.client:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(
                    client=client, slug=self.options.show)
        else:
            show = Show.objects.get(slug=self.options.show)

        self.one_show(show)

        return

    def add_more_options(self, parser):
        # parser.add_option('--offset_hours', type="int",
        #   help="adjust time to deal with clock in wrong time zone.")
        # parser.add_option('--offset_seconds', type="float",
        #    help="adjust time to deal with clock wrong.")

        parser.add_option('--time_source',
           help="one of fn, fs, frame, gst, un, auto\n" \
             "(file name, file system, dv frame, gst lib, UN files, auto)")
        parser.add_option('--ext',
           help="only hit this ext")
        parser.add_option('--subs',
           help="string to use for subs stuff that makes me cry.")
        parser.add_option('--delete-unknown', action='store_true',
            help="Delete any file records from the database, if we can't "
                 "find them on disk.")

    def add_more_option_defaults(self, parser):
        # parser.set_defaults(offset_hours=0)
        #  parser.set_defaults(offset_seconds=0)
        parser.set_defaults(time_source="auto")


if __name__=='__main__':
    p=ts_rf()
    p.main()

