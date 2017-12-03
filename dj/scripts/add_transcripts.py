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

        for l in open(filename, encoding='iso-8859-1').read().split('/n'):
            timestamp, text = l[:11], l[12:]
            timestamp = date + ' ' + timestamp
            print(timestamp)
            timestamp = datetime.datetime.strptime(timestamp[:-3], '%m%d%Y %H:%M:%S' )
            print(timestamp)
            print(text)
            ret.append( {'timestamp':timestamp, 'text':text} )

        return ret

    def find_eps(self, transcript , eps):
        # return a list of eps that likely belong to transcript

        tstart = transcript[0]['timestamp']
        tend = transcript[-1]['timestamp']

        founds=set()
        for ep in eps:
            if tstart <= ep.end and tend >= ep.start:
                founds.add(ep)

        return founds

    def slice_dice(self, img_page, src_name, show, eps):

        # and connect the img object to episodes
        # imgname = self.ass_one( img, text, locs, eps )

        # words to look for in set header:
        words = ["Kit Number",  "Cam Op", "Audio op",
        "Pre Day check",
        "Replace Batteries in mics",
        "Post production", "Scanned",
        "System date and time"]
        hit_count=0
        for word in words:
            if word.lower() in text.lower():
                hit_count +=1
                # print word, hit_count
        first_page_of_set = hit_count >= 3

        """
        first_page_of_set = src_base in [
                "pygoth-{:03d}.ppm".format(i-1) for i in [
                    1, 4, 7, 9, 12, 14, 17, 20, ]]
        """

        if first_page_of_set:
            start = 1000 #1100 # 728 # 820 # 995
            end = 1528 # 1705 # 1071 # 1370 # 1547
            bands= 3
            suffix='a'
        else:
            start = 730 # 802 # 400 # 577
            end = 1255 # 1318 # 960 # 1127
            bands= 4
            suffix='b'

        page = 3450 # 2338 # 3216

        head = float(start)/float(page)
        band = float(end-start)/float(page)
        fudge = 0.02

        im = Image.open(src_name)
        w, h = im.size
        src_base = os.path.basename(src_name)
        for i in range(bands):

            box = im.crop(
                (0, int(h * (head + band * i )),
                 w, int(h * (head + band * (i+1) + fudge) ))
                        )

            png_name = '{}-{}{}.png'.format(
                    os.path.splitext(src_base)[0], i, suffix)
            print(png_name)
            box.save( os.path.join( self.show_dir, "img", png_name ))

            # upload it
            if self.options.rsync:
                self.file2cdn(show, os.path.join( "img", png_name ))

            # put the png name is in the db
            img_band,created = Image_File.objects.get_or_create(
                    show=show,
                    filename=png_name,)

            # ocr and connect the img object to episodes
            text = self.ocr_img(
                    os.path.join( self.show_dir, "img", png_name ))
            img_band.text = text
            img_band.save()

            # self.ass_one( img_band, text, locs, eps )
            founds = self.find_eps(text, eps )
            for found in founds:
                img_band.episodes.add(found)
                img_page.episodes.add(found)


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

            transcript = self.parse_transcript_file(
                    os.path.join( self.show_dir, "transcripts", transcript_filename ))

            founds = self.find_eps(transcript, eps )
            for found in founds:
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

