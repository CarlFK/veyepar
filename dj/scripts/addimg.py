#!/usr/bin/python

# Adds png files to the Image table
# uses ocr to link them to an episode


"""
gscan2pdf
http://gscan2pdf.sourceforge.net

/home/carl/temp/ajschi_2016-11-17.pdf

scan paper to pdf:
  snap scan on mac, Automatic resolution, Auto color detection

drop pdf in ~/Videos/veyepar/client/show/img/
extract images:
pdfimages pyohio2014reviewsheets.pdf pyohio2014reviewsheets

# if pdfimages doesn't work out, use convert
# convert -monochrome -density 300 pyohio2014reviewsheets.pdf pyohio2014reviewsheets.png

pip install pyocr
sudo apt install tesseract-ocr-eng tesseract-ocr

python addimg.py --rsync
"""

import os
import subprocess

import re

import pyocr

from process import process

from main.models import Client, Show, Location, Episode, Image_File

from PIL import Image


"""
pyohio 2019
size = 2592 x 3450,


something else:
page: 2544x3296
start 880
end: 1421

these were some dimenions I played around with
box1 = (
    0, 1066,
    3386, 2000
)
box2 = (
    0, 1500,
    3386, 2500
)
box3 = (
    0, 2500,
    3386, 3500
)

"""

class add_img(process):

    def ocr_img(self, imgname):

        """
        To use a non-standard language pack named foo.traineddata, set the TESSDATA_PREFIX environment variable so the file can be found at TESSDATA_PREFIX/tessdata/foo.traineddata and give Tesseract the argument -l foo.
        """

        tools = pyocr.get_available_tools()
        tool = tools[0]
        text = tool.image_to_string(
            Image.open(imgname),
            lang='eng',
            builder=pyocr.builders.TextBuilder(),
        )

        print(text)

        return text

    def to_png(self, src, dst):
        convert_cmd = ['convert', src, dst]
        self.run_cmd(convert_cmd)
        return dst

    def find_eps(self, text, eps):
        # return a list of eps that likely belong to text
        text = re.sub(r'\n[\n ]+', '\n', text)

        def is_in( obj, attrib, text ):
            # check if obj.attrib is in text
            val = str(getattr(obj, attrib))
            if val in ['','2014',]:
                # blacklisted values
                return
            if val.lower() in text:
                print("found", attrib, val)
                ret=True
            else:
                ret=False
            return ret

        founds=set()
        for ep in eps:
            for attr in ["id", "name", "authors"]:
                if is_in( ep, attr, text ):
                    founds.add(ep)

        return founds

    def slice_dice(self, img_page, src_name, show, eps):

        # ocr
        # and connect the img object to episodes
        text = self.ocr_img(src_name)

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
            start = 539 # 1014 # 982 # 1000 #1100 # 728 # 820 # 995
            end = 908 # 1560 # 1526 # 1528 # 1705 # 1071 # 1370 # 1547
            bands= 3
            suffix='a'
        else:
            start = 267 # 622 # 584 #730 # 802 # 400 # 577
            end =  636 # 1169 # 1126 # 1255 # 1318 # 960 # 1127
            bands= 4
            suffix='b'

        page = 3450 # 2338 # 3216

        head = float(start)/float(page)
        band = float(end-start)/float(page)
        fudge = 0.025 # I'm not really sure what the unit is)

        im = Image.open(src_name)
        w, h = im.size
        src_base = os.path.basename(src_name)
        for i in range(bands):

            box = im.crop(
                (0, int(h * (head + band * i - fudge )),
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

            founds = self.find_eps(text, eps )
            for found in founds:
                img_band.episodes.add(found)
                img_page.episodes.add(found)


    def one_page(self, src_base, show, eps):

        """
        convert ppm to png
        upload png to cdn
        add png name to db under current show
        ocr png page
        link to episodes it may be a part of
        chop into strips
        add strips to db/cdn, ocr, link
        """

        print(src_base)
        # foo.ppm

        # the scan that was extracted from the pdf
        src_name = os.path.join( self.show_dir, "img", src_base )

        # the base png name to use for the db and html
        # foo.png
        png_base = os.path.splitext(src_base)[0] + ".png"

        # create the png (and add the full path to png_name
        # (png because browsers don't suppport ppm)
        self.to_png(src_name,
            os.path.join( self.show_dir, "img", png_base ))

        # upload it
        if self.options.rsync:
            png_branch = os.path.join( "img", png_base )
            print(png_branch)
            self.file2cdn(show, png_branch)

        # make sure the png name is in the db
        img_page,created = Image_File.objects.get_or_create(
                show=show,
                filename=png_base,)

        if not self.options.dumb:
            self.slice_dice(img_page, src_name, show, eps)


    def one_ep(self, src_base, show, eps):

        """
        hack for slide images
        only one episode allowed
        upload png to cdn
        add png name to db under current show and
        link to episode
        """
        # img_dir = "custom/pytests/png"
        img_dir = "img"

        # print()
        # print(1, img_dir)
        # print(2, src_base)
        # foo.ppm

        # the scan that was extracted from the pdf
        src_name = os.path.join( self.show_dir, img_dir, src_base )
        print(3, src_name)

        # upload it
        if self.options.rsync:
            img_branch = os.path.join( img_dir, src_base )
            print(4, img_branch)
            self.file2cdn(show, img_branch)


        # make sure the png name is in the db
        img,created = Image_File.objects.get_or_create(
                show=show,
                filename=img_branch,)

        if created:
            for ep in eps:
                img.episodes.add(ep)


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
      if self.args:
          eps = eps.filter(id__in=self.args)

      # locs = Location.objects.filter(show=show)

      self.set_dirs(show)
      ep_dir=os.path.join(self.show_dir,'img')
      # ep_dir=os.path.join(self.show_dir,'custom/pytests/png')
      if self.options.verbose:
          print("ep_dir:", ep_dir)

      for dirpath, dirnames, filenames in os.walk(ep_dir,followlinks=True):
          d=dirpath[len(ep_dir)+1:]
          if self.options.verbose:
              print("checking...", dirpath, d, dirnames, filenames)
          for f in filenames:
              if os.path.splitext(f)[1] in [
                      ".png", ".ppm", ".pbm", ".jpg" ]:
                  print(f, end='')

                  if self.options.base and \
                          not f.startswith(self.options.base):
                        print(" doesn't match the 'filter'.")
                        continue

                  self.one_page(os.path.join(d,f),show,eps)
                  # self.one_ep(os.path.join(d,f),show,eps)

                  if self.options.test:
                      print("...Test mode, only doing one.")
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
    p=add_img()
    p.main()

