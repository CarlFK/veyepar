#!/usr/bin/python

# Adds png files to the Image table
# uses ocr to link them to an episode

# convert -monochrome -density 300 pyohio2014reviewsheets.pdf pyohio2014reviewsheets.png

import os
import subprocess

from process import process

from main.models import Client, Show, Location, Episode, Image_File

class add_img(process):

    def ocr_ass_one(self, img, src, locs, eps):

        imgname = os.path.join( self.show_dir, src)
        ocr_cmd = ['tesseract', imgname, '/tmp/text']
        print ocr_cmd
        print ' '.join(ocr_cmd)
        p = subprocess.Popen(ocr_cmd)
        x = p.wait()
        text = open('/tmp/text.txt').read().decode('UTF-8')
        """
        To use a non-standard language pack named foo.traineddata, set the TESSDATA_PREFIX environment variable so the file can be found at TESSDATA_PREFIX/tessdata/foo.traineddata and give Tesseract the argument -l foo.
        """
        img.text = text

        # scan the eps and locs to see if we can find a link
        def is_in( img, ep, a, text ):
            val = unicode(getattr(ep, a))
            if val in ['','2014',]:
                # blacklisted values
                return
            if val.lower() in text:
                print "found", a, val
                img.episodes.add(ep)
                img.save()

        for ep in eps:
            is_in( img, ep, "id", text )
            is_in( img, ep, "conf_key", text )
            is_in( img, ep, "name", text )
            is_in( img, ep, "authors", text )

        for loc in locs:
            if loc.name.lower() in text.lower():
                print "found loc", loc
                img.location = loc

        img.save()


    def one_file(self,pathname,show, locs, eps):
        print pathname,

        img,created = Image_File.objects.get_or_create(
                show=show, 
                filename=pathname,)

        if created or self.options.force: 
            print "added to db"
            src = os.path.join( "img", pathname )

            self.ocr_ass_one( img, src, locs, eps )

            if self.options.rsync:
                self.file2cdn(show, src)

        else: 
            print "in db"
   
    def one_show(self, show):
      if self.options.verbose:  print "show:", show.slug
      if self.options.whack:
          Image_File.objects.filter(show=show).delete()

      eps = Episode.objects.filter(show=show)
      locs = Location.objects.filter(show=show)

      self.set_dirs(show)
      ep_dir=os.path.join(self.show_dir,'img')

      for dirpath, dirnames, filenames in os.walk(ep_dir,followlinks=True):
          d=dirpath[len(ep_dir)+1:]
          if self.options.verbose: 
              print "checking...", dirpath, d, dirnames, filenames 
          for f in filenames:
              self.one_file(os.path.join(d,f),show,locs,eps)

              if self.options.test:
                  print "Test mode, only doing one."
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

if __name__=='__main__': 
    p=add_img()
    p.main()

