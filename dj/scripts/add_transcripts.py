#!/usr/bin/python

# Adds transcript files to the Image table
# uses timestamp of firlst line to link them to an episode


import datetime
import os

from process import process

from main.models import Client, Show, Location, Episode, Image_File


class add_transcript(process):

    def parse_transcript_file(self, filename):
        print(filename)

        date = filename.split(' ',1)[0][-8:]
        print(date)

        ret = []

        for l in open(filename, encoding='iso-8859-1').read().splitlines():
            if not l: continue

            timestamp, text = l[:11], l[12:]
            timestamp = date + ' ' + timestamp
            timestamp = datetime.datetime.strptime(timestamp[:-3], '%m%d%Y %H:%M:%S' )
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
                    elif s==1 and l['timestamp']<=ep.end:
                        print("end line: {}".format(l))
                        s=2

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


    def one_show(self, show):

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

    def work(self):
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

