#!/usr/bin/python

# makes a transcription file from the master for the day.

import datetime
import os
from pprint import pprint

import pycaption

from process import process

from main.models import Client, Show, Location, Episode, Cut_List


class add_transcript(process):

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


    def v1()

        # transcript_filename = '12022017 North Bay Day 1.txt'
        # transcript = self.parse_transcript_file( os.path.join( self.show_dir, "transcripts", transcript_filename ))

    def v2()
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

                # print("import sys; sys.exit()"); import code; code.interact(local=locals())




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

    def process_ep(self, episode):
        return v3(episode)

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

    def xwork(self):
        """
        find and process show
        """
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)
            self.one_show(show)

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

