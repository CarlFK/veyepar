#!/usr/bin/python

"""
tsraw.py - timestamp raw files
gets start/end times of raw files

Gets start from one of:
metadata via gst.discover()
the file name (assumes yy_mm_dd/hh_mm_ss.dv format)
the file system time stamp,
the first frame of the dv

duration (in seconds) based on file size / BBF*FPS
gst.discover()
last frame ?

"""

import argparse
import datetime
import pathlib
import pprint
import pytz
import os
import re
import subprocess

import exiftool
from pymediainfo import MediaInfo

import gi
gi.require_version('Gst', '1.0')
from gi.repository import Gst

from gi.repository import GObject
GObject.threads_init()
Gst.init(None)

gi.require_version('GstPbutils', '1.0')
from gi.repository import GstPbutils


def get_start( pathname, time_source ):

    """
    get the start of this clip
    dv.filename generally looks like this: 2012-01-14/10:01:34.dv
    parse the dir and filename strings.
    or use the filesystem_create
    """

    # 3 ways of getting the datetime this file started

    def fs_time(pathname):
        # get timestamp from filesystem
        st = os.stat(pathname)
        ts_start=datetime.datetime.fromtimestamp( st.st_mtime )
        return ts_start

    def parse_name(pathname):
        # print("parse_name")
        # parse string into datetime
        # expects room/yyy-mm-dd/hh_mm_ss-x.ext
        # or room/yyy-mm-dd/GMT20230511-232712_Recording_2880x1800.mp4
        # >>> "GMT20231109-235900_Recording_2880x1800.mp4"[:29]
        # 'GMT20231109-235900_Recording_'


        p = pathlib.PurePath(pathname)
        filename = p.stem # GMT20230511-232712_Recording_2880x1800

        # for Tegus Zoomy system
        # start = datetime.datetime.strptime(filename,'GMT%Y%m%d-%H%M%S_Recording_2880x1800')
        # start = datetime.datetime.strptime(filename,'GMT%Y%m%d-%H%M%S_Recording_1920x1120')
        start = datetime.datetime.strptime(filename[:29],'GMT%Y%m%d-%H%M%S_Recording_')
        # start += datetime.timedelta(hours=-5) # for chicago time
        gmt = pytz.timezone('GMT')
        # pytz.timezone('America/Chicago')
        start = start.replace( tzinfo=gmt ).astimezone()

        return start

        # remove extention
        filename = os.path.splitext(pathname)[0]

        # dvswitch appends -n in the event of filename colisions.
        # for start, dupe time is fine, so drop the -n for parsing
        if filename[-2]=='-': filename = filename[:-2]

        # for now, the last dir is the date, and the file is time:
        filename='/'.join(filename.split('/')[-2:])

        # swap : for _ (so either : or _ can be used in the filename)
        filename = filename.replace(':','_')

        # parse
        start=datetime.datetime.strptime(filename,'%Y-%m-%d/%H_%M_%S')
        return start

    def re_name(pathname):
        # print("re_name...")
        # parse string into datetime useing RE

        dt_re = r".*/(?P<year>\d+)-(?P<month>\d+)-(?P<day>\d+).*/(?P<hour>\d+)_(?P<minute>\d+)_(?P<second>\d+)"


        dt_o = re.match(dt_re, pathname)
        dt_parts = dt_o.groupdict()
        print(dt_parts)

        dt_parts = {k:int(v) for k,v in list(dt_parts.items())}
        print(dt_parts)

        start=datetime.datetime( **dt_parts )
        print(start)

        return start

    def PyExifTool(pathname):
        # use PyExifTool to read Time Code
        """
        >>> metadata['H264:TimeCode']
        u'03:25:30:12'
         u'H264:DateTimeOriginal': u'2015:11:03 10:22:23+00:00',
        """

        with exiftool.ExifTool() as et:
            metadata = et.get_metadata(pathname)
        dt = metadata['H264:DateTimeOriginal']

        start=datetime.datetime.strptime(dt,'%Y:%m:%d %H:%M:%S+00:00')
        # print(start)
        return start

    def frame_time(pathname):
        # get timestamp from first frame
        pass

    def gst_discover_start(pathname):
        # get start time using gstreamer to read the media file header
        # print("gst_discover_start")

        print(pathname)

        """
     If you add an 'audioparse' element (or 'rawaudioparse' in >= 1.9/git
     master) after filesrc and configure it with the right properties, it
     should be able to report the duration correctly.
        """

        discoverer = GstPbutils.Discoverer()
        d = discoverer.discover_uri('file://{}'.format(pathname))
        tags= d.get_tags()
        dt=tags.get_date_time("datetime")[1]

        # import code; code.interact(local=locals())

        # print(dt.to_iso8601_string())
        start = datetime.datetime(
                year=dt.get_year(),
                month=dt.get_month(),
                day=dt.get_day(),
                hour=dt.get_hour(),
                minute=dt.get_minute(),
                second=dt.get_second(),
                )

        return start

    def un(pathname):
        # files from the UN.

         # date is in the file name
         # time is in other: time_code_of_first_frame
         # 1672828_DMOICT Open Camps CR7 8AM-12PM 16 JULY 16.mov

        year = "2016"
        month = 'JULY'
        day = pathname.split(month)[0].split()[-1]

        media_info = MediaInfo.parse(pathname)
        t3=media_info.tracks[3]
        time = t3.time_code_of_first_frame
        # dt = "{year}-{month}-{day} {time}".format(
        #        year=year, month=month, day=day, time=time)
        # na, that didn't work

        # try this
        dt = media_info.tracks[0].recorded_date
        # '2024-04-19 19:07:10-05:00'
        print(dt)
        start = datetime.datetime.strptime(dt,'%Y-%m-%d %H:%M:%S-05:00')

        print( start )

        return start

        # d+_DMOICT...move stuff so it errors if it finds something else
        start_date_re = r".*/" + date_re + ".*/\d+_DMOICT.*\.mov"

        start_date_o =  re.match(start_date_re, pathname)
        dt_parts = start_date_o.groupdict()
        print("date_parts:", dt_parts)


        cmd = ['mediainfo',
                '--Inform=Video;%TimeCode_FirstFrame%',
                pathname ]
        p = subprocess.Popen(
                cmd,
                stdout = subprocess.PIPE )
        stdout = p.stdout.read()
        # '07:50:00:00\n'

        # time_code = stdout.strip().split(':')

        start_time_re = time_re + rb":\d\d\n"

        start_time_o =  re.match(start_time_re, stdout)
        start_time_d = start_time_o.groupdict()
        print("start_time_d:",start_time_d)

        dt_parts.update(start_time_d)
        pprint.pprint(dt_parts)

        dt_parts = {k:int(v) for k,v in list(dt_parts.items())}
        print(dt_parts)

        start=datetime.datetime( **dt_parts )
        print(start)

        return start


    def auto(pathname):
        # try to figure out what to use
        # print("auto...")

        time_re = r".*(?P<h>\d+)_(?P<m>\d+)_(?P<s>\d+)\."
        ext = os.path.splitext(pathname)[1]

        if re.match( time_re, pathname ) is not None:
            start = re_name(pathname)

        elif ext == ".dv":
            start = parse_name(pathname)

        elif ext == ".MTS":
            start = PyExifTool(pathname)

        else:
            start = gst_discover_start(pathname)

        return start

    # get_start() starts here..

    # wacky python case statement
    start = {'fn':parse_name,
             'fs':fs_time,
             'frame':frame_time,
             'gst':gst_discover_start,
             'un':un,
             'auto':auto,
             }[time_source](pathname)

    return start

def get_duration(pathname):

    def fs_size(pathname):
        # calc duration from size

        # get timestamp from filesystem
        st = os.stat(pathname)
        filesize=st.st_size

        frames = filesize/120000
        dv_seconds = frames/29.98

        return dv_seconds

    def gst_discover_duration(pathname):
        # use gstreamer to find get_duration
        # print("gst_discover_duration")
        discoverer = GstPbutils.Discoverer()
        try:
            d = discoverer.discover_uri('file://{}'.format(pathname))
            seconds = d.get_duration() / float(Gst.SECOND)
        except gi.repository.GLib.GError:
            seconds=None
            seconds=6300

        return seconds

    def mi(pathname):
        media_info = MediaInfo.parse(pathname)
        durations = media_info.tracks[0].other_duration
        # ['15 s 371 ms', '15 s 371 ms', '15 s 371 ms', '00:00:15.371', '00:00:15;13', '00:00:15.371 (00:00:15;13)']
        duration = durations[3]
        h,m,s = [float(i) for i in duration.split(':')]
        seconds = h*3600 + m*60 + s

        return seconds

    if os.path.splitext(pathname)[1]==".MTS":
        seconds = mi(pathname)

    elif os.path.splitext(pathname)[1]==".dv":
        seconds = fs_size(pathname)

    # elif os.path.splitext(pathname)[1]==".ts":
    #    seconds = 60 * 30
    else:
        seconds = gst_discover_duration(pathname)

    return seconds

    # return start, seconds

def test(pathname, ts="all"):
    print(pathname, ts)

    if ts == "all":
        for ts in [ 'fn', 'fs', 'frame', 'gst', 'un', 'auto', ]:
            try:
                print("Start (using {ts}):".format(ts=ts),
                        get_start(pathname, ts) )
            except (ValueError,AttributeError) as e:
                print(e)

    else:

        print("Start (using {}):".format(ts), get_start(pathname, ts) )

    print("Duration (using {}):".format(ts), get_duration(pathname))

    return

def make_parser():

    parser = argparse.ArgumentParser(description="""
    prints the start time and durration of a media file.
    """)
    parser.add_argument('filenames', nargs='+')
    parser.add_argument('--time-source',
       help="one of fn, fs, frame, gst\n" \
         "(file name, file system, dv frame, gst lib, auto)",
         default="all")

    # parser.add_argument('--ext',
    #   help="only hit this ext")

    return parser


def main():

    parser = make_parser()
    args = parser.parse_args()

    for filename in args.filenames:
        test(filename, args.time_source)

    """
    filenames = [
            "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Stowe_Hall/2015-11-14/graphics swang 11:14/Clip1GTK19.mov",
    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Stowe_Hall/2015-11-14/video swang 11:14/Clip1ATK1.mov",

    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Collins_Auditorium/2015-11-14/Saturday Morning Camera/SC1ATK103.mov",
    "/home/carl/Videos/veyepar/nodevember/nodevember15/dv/Collins_Auditorium/2015-11-14/Saturday Morning GFX/Clip1ATK653.mov",
    ]

    for filename in filenames:
        test(filename)
    """
    # test("/home/carl/temp/segment-0.ts")
    # d = u"/home/carl/mnt/rad/Videos/veyepar/big_apple_py/pygotham_2016/dv/Room_CR7/2016-07-16/"

    # d = "/home/carl/temp/"
    # test(d + "1672828_DMOICT Open Camps CR7 8AM-12PM 16 JULY 16.mov", "all")

    # test(d + "12_14_09.ts", 'auto')
    # test("/home/carl/temp/1672828_DMOICT.mov", 'all')


if __name__=='__main__':
    main()


