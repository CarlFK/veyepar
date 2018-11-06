#!/usr/bin/python

# makes a transcription file from the master for the day.

import datetime
import os
from pprint import pprint

import pycaption

from process import process

from main.models import Client, Show, Location, Episode, Cut_List

def get_transcriptions(cls):

    """
    loop over the cuts because that is where the data is now.
    """

    transcriptions = []
    video_time = 0

    for cl in cls:

        for c in cl.comment.split('\n'):

            if c.startswith('TS'):
                kv=c.split('=',1)[1].strip().split(' ',1)
                transcription = {}
                transcription['start']={
                    'timestamp':kv[0],
                    'text': kv[1] if len(kv)>1 else None,
                    'wallclock': cl.get_start_wall(),
                    'video_time': video_time,
                    }

            if c.startswith('TE'):
                kv=c.split('=',1)[1].strip().split(' ',1)
                transcription['end']={
                    'timestamp':kv[0],
                    'text': kv[1] if len(kv)>1 else None,
                    'wallclock': cl.get_end_wall(),
                    }

                transcriptions.append(transcription)
                transcription = None

        video_time += cl.duration()
        # print("vt: {}".format(video_time))

    return transcriptions


class add_transcript(process):

    ready_state=None
    # jr333

    def parse_transcript_file(self, filename):
        # parse the human readable format.

        print(filename)

        date = filename.split(' ',1)[0][-8:]
        print(date)

        sync = datetime.timedelta(seconds=11)

        ret = []

        for l in open(filename, encoding='iso-8859-1').read().splitlines():
            if not l: continue

            timestamp, text = l[:11], l[12:]
            timestamp = date + ' ' + timestamp
            timestamp = datetime.datetime.strptime(timestamp[:-3], '%m%d%Y %H:%M:%S' )
            timestamp -= sync

            ret.append( {'timestamp':timestamp, 'text':text} )

        return ret

    def find_eps(self, transcript, eps):
        # return a list of eps that likely belong to transcript

        tstart = transcript[0]['timestamp']
        tend = transcript[-1]['timestamp']

        founds=set()
        for ep in eps:
            if tstart <= ep.end and tend >= ep.start:
                print("file start/end: {} / {}".format(tstart,tend))
                print("ep start/end: {} / {}".format(ep.start,ep.end))
                founds.add(ep)
                s=0
                for l in transcript:
                    # print(l['timestamp'])
                    if s==0 and l['timestamp']>=ep.start:
                        print("start line: {}".format(l))
                        s=1
                    elif s==1 and l['timestamp']>=ep.end:
                        print("end line +1: {}".format(l))
                        s=2

                    if s==1:
                        d = l['timestamp'] - ep.start
                        seconds = int(d.total_seconds())
                        hms = seconds//3600, (seconds%3600)//60, seconds%60
                        hms = "{}:{}:{}".format(*hms)
                        print("{}: {}".format( hms, l['text']))

        return founds

    def one_file(self, transcript_filename, show, locs, eps):

        # upload it
        if self.options.rsync:
            wut = os.path.join( "transcripts", transcript_filename )
            print(wut)
            self.file2cdn(show, wut)

        # make sure the transcript_filename is in the db
        img_page,created = Image_File.objects.get_or_create(
                show=show,
                filename=transcript_filename)

        if not self.options.dumb:

            transcript = self.parse_transcript_file( os.path.join(
                        self.show_dir, "transcripts", transcript_filename ))

            founds = self.find_eps(transcript, eps )

            for found in founds:
                print("found: {}".format(found))
                img_page.episodes.add(found)


    def v1():

        transcript_filename = '12022017 North Bay Day 1.txt'
        transcript = self.parse_transcript_file( os.path.join( self.show_dir, "transcripts", transcript_filename ))

    def v2():
        transcript_filename = '12022017 NBPY SCC.scc'
        transcript_pathname = os.path.join( self.show_dir,
              "assets", "transcripts", transcript_filename )

        caps = open(transcript_pathname, encoding='iso-8859-1').read()
        reader = pycaption.detect_format(caps)
        transcript = reader().read(caps)
        language = transcript.get_languages()[0] # ['en-US']
        lines = transcript.get_captions(language)

        cls = Cut_List.objects.filter(
            episode=episode, apply=True).order_by('sequence')

        # video_start = None

        ep_t_out_filename = os.path.join( self.show_dir,
                "transcripts", episode.slug + ".scc" )

# head 12022017\ North\ Bay\ Day\ 1.txt
# 10:06:56:00 >> Hi, everyone!  Welcome to
        transcript_start = datetime.datetime.strptime(
                "12022017 10:06:56", '%m%d%Y %H:%M:%S' )

        with open(ep_t_out_filename,'w') as f:

            segs=[]
            for cl in cls:

                start = cl.get_start_wall()
                end = cl.get_end_wall()
                segs.append( (start,end) )

                # wall time of the start of the first clip:
                # if video_start is None:
                #    video_start = start

                """
                loffset_ms = (
                        transcript_start - video_start
                        ).total_seconds() * 1000

                print( {start





                for l in transcript:
                  if start <= l['timestamp']  <= end:

                      offset = l['timestamp'] - video_start
                      seconds = int(offset.total_seconds())
                      hms = seconds//3600, (seconds%3600)//60, seconds%60
                      hms = "{}:{}:{}".format(*hms)

                      l = "{}: {}".format( hms, l['text'])
                      f.write(l+'\n')

                """
        pprint( segs )
        for s,e in segs:
            # print("s: {}".format(s))
            # print("e: {}".format(e))
            # df='%Y-%m-%d %H:%M:%S'
            df="%H:%M:%S"
            print( "{} - {}".format ( s.strftime(df), e.strftime(df) ) )

    def v3(self, episode):

        ## Get transcription data
        transcript_filename = '12022017 NBPY SCC.scc'
        transcript_pathname = os.path.join( self.show_dir,
              "assets", "transcripts", transcript_filename )
        caps = open(transcript_pathname, encoding='iso-8859-1').read()

        transcript = pycaption.SCCReader().read( caps )
        language = transcript.get_languages()[0] # ['en-US']
        captions = transcript.get_captions( language )

        ## Get markes for this video
        cls = Cut_List.objects.filter(
            episode=episode, apply=True).order_by('sequence')
        transcriptions = get_transcriptions(cls)

        for transcription in transcriptions:
            pprint(transcription)

            state = 0
            for c in captions:

                if c.format_start() == \
                        transcription['start']['timestamp']:

                    state=1
                    offset = c.start - transcription['start']['video_time'] * 1000000
                    wc = transcription['start']['wallclock']
                    # walltime that transcription file started.
                    epoch = wc - datetime.timedelta(microseconds = c.start )

                    print( "c: {c}\nc.start: {start}\nwall_clock: {wallclock}".format(
                        c=c, start=c.start, wallclock=wc ) )
                    print("epoch: {}".format( epoch ))

                    print("import sys; sys.exit()"); import code; code.interact(local=locals())

                if state==1:

                    if c.format_start() == \
                            transcription['end']['timestamp']:
                        c.nodes[0].content=\
                                transcription['end']['text']
                        state = 0

                    c.start -= offset
                    c.end -= offset


    def v4(self, episode):

        epoch = datetime.datetime(2017, 12, 2, 10, 6, 36, 841067)
        # 2017-12-02 10:06:36.841067

        ## Get transcription data
        transcript_filename = '12022017 NBPY SCC.scc'
        transcript_pathname = os.path.join( self.show_dir,
              "assets", "transcripts", transcript_filename )
        caps = open(transcript_pathname, encoding='iso-8859-1').read()

        transcript = pycaption.SCCReader().read( caps )
        language = transcript.get_languages()[0] # ['en-US']
        captions = transcript.get_captions( language )

        cls = Cut_List.objects.filter(
            episode=episode, apply=True).order_by('sequence')
        # transcriptions = get_transcriptions(cls)
        for cl in cls:
            print( cl.get_start_wall() )

            cl_start = ( cl.get_start_wall() - epoch
                    ).total_seconds() * 1000000
            cl_end = ( cl.get_end_wall() - epoch
                    ).total_seconds() * 1000000

            state = 0
            for c in captions:

                # look for start
                if state == 0:
                    if c.start > cl_start - 4000000:
                        print( "start: {}".format(cl.start))
                        state = 1

                # print a bunch of start
                if state == 1:
                    print("{} {}".format(c.format_start(), c.get_text() ))

                    if c.start > cl_start + 4000000:
                        print()
                        state = 2

                # look for end
                if state == 2:
                    if c.start > cl_end - 4000000:
                        print( "end: {}".format(cl.end))
                        state = 3

                # print a bunch of end
                if state == 3:
                    print("{} {}".format(c.format_start(), c.get_text() ))

                    if c.start > cl_end + 4000000:
                        print()
                        state = 4

        # print("import sys; sys.exit()"); import code; code.interact(local=locals())


    def v6(self, episode):
        # last one used for nbpy 17
        # now using it for nbpy 18

        def show_near( x, wall ):
            # x: "start" or "end"
            # wall: cut datetime

            if True or self.options.verbose:
                print("show_near( x={}, wall={}".format (x, wall))

            start_fudge, end_fudge = 290, 26

            # epoch = datetime.datetime(2017, 12, 2, 10, 6, 36, 841067)
            # 2017-12-02 10:06:36.841067
            epoch = datetime.datetime(2018, 11, 3, 10, 8, 52)

            from_epoch = (wall - epoch).total_seconds() * 1000000
            print( "from_epoch:", from_epoch )

            #print("looking for: '01:19:56.825 --> 01:19:58.827\nPLEASE WELCOME, LORENA MESA.\n4796825366.666667\ns:13:34:33 is \n")

            state = 0
            for c in captions:
                if self.options.verbose:
                    print(c)
                    print(c.start)

                if state == 0:
                    if c.start > from_epoch - start_fudge * 1000000:
                        print( "{}: {}".format(x, wall))
                        state = 1

                if state == 1:

                    # 00:10:36.669 636669366.6666665
                    # 2039-01-06 06:44:58.666667
                    # 122330633.33333349 >> HI, EVERYONE. THANK YOU SO

                    print(
                        c.format_start(), c.start,
                        epoch + datetime.timedelta(seconds=c.start/1000000),
                        int((from_epoch - c.start)/1000000),
                        c.get_text()
                        )

                    if c.start > from_epoch + end_fudge * 1000000:
                        print()
                        return

        ## Get transcription data
        # transcript_filename = '12022017 NBPY SCC.scc'
        transcript_filename = 'NBPYTHONDAYONE.scc'
        transcript_pathname = os.path.join( self.show_dir,
              "assets", "transcripts", transcript_filename )
        caps = open(transcript_pathname, encoding='iso-8859-1').read()

        transcript = pycaption.SCCReader().read( caps )
        language = transcript.get_languages()[0] # ['en-US']
        captions = transcript.get_captions( language )

        cls = Cut_List.objects.filter(
            episode=episode, apply=True).order_by('sequence')

        show_near( "start", cls.first().get_start_wall() )
        show_near( "end", cls.last().get_end_wall() )


    def v7(self, episode):
        """
        ffmpeg -i k.mp4 -i k.srt -c copy -c:s mov_text outfile.mp4
        """

    def process_ep(self, episode):
        # return self.v3(episode)
        return self.v6(episode)

    def xone_show(self, show):

      self.show = show
      self.client = show.client

      if self.options.verbose:  print("show:", show.slug)
      if self.options.whack:
          Image_File.objects.filter(show=show).delete()

      eps = Episode.objects.filter(show=show)
      if self.options.day:
          eps = eps.filter(start__day=self.options.day)
      if self.options.room:
          eps = eps.filter(location__slug=self.options.room)

      locs = Location.objects.filter(show=show)

      self.set_dirs(show)
      ep_dir=os.path.join(self.show_dir,'transcripts')
      if self.options.verbose:
          print("ep_dir:", ep_dir)

      for dirpath, dirnames, filenames in os.walk(ep_dir,followlinks=True):
          d=dirpath[len(ep_dir)+1:]
          if self.options.verbose:
              print("checking...", dirpath, d, dirnames, filenames)
          for f in filenames:
              if os.path.splitext(f)[1] in [
                      ".txt", ]:
                  print(f)

                  if self.options.base and \
                          not f.startswith(self.options.base):
                      # doesn't match the 'filter'
                      continue

                  self.one_file(os.path.join(d,f),show,locs,eps)

                  if self.options.test:
                      print("Test mode, only doing one.")
                      return


    def add_more_options(self, parser):
        parser.add_option('--rsync', action="store_true",
            help="upload to DS box.")

        parser.add_option('--base',
            help="source filename base.")

        parser.add_option('--dumb', action="store_true",
            help="just add to show, no ocr, no guessing.")

if __name__=='__main__':
    p=add_transcript()
    p.main()

