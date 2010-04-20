#!/usr/bin/python

"""
mkthumbs.py - find thumbs
ocr untill we find some text
"""

import  os

import gsocr
# import ocrdv

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class add_dv(process):

    def one_dv(self, dir, dv ):
        
        pathname = os.path.join(dir,dv.filename)
        print "dv:", pathname

        if not os.path.exists("%s.png" % dv.basename ):
            p=gsocr.Main(pathname)
            gsocr.gtk.main()
            if p.words:
                dv.ocrtext=p.words
                # dv.thumbnail=p.imgname
                dv.save()

        """
        # code from py-ffmpeg
        ocrtext,img=ocrdv.ocrdv(pathname)

        if img:
            imgname = os.path.join(dir,dv.basename()+".png")
            img.save(imgname,'png')
            dv.thumbnail = imgname
            dv.save()
        """

	return p.basename

    def process_eps(self,episodes):
      # this never gets called because this processes files, not episodes.
      for ep in episodes:
          print ep.location.slug
          dir=os.path.join(self.show_dir,'dv',ep.location.slug)
          dvs = Raw_File.objects.filter(cut_list__episode=ep)
          for dv in dvs:
              imgname=self.one_dv(dir,dv)
              print imgname
              # ep.thumbnail = imgname
              # ep.save()
              return
          

    def one_loc(self,location,dir):
      for dv in Raw_File.objects.filter(location=location):
          imgname=self.one_dv(dir,dv)
          print imgname


    def one_show(self, show):
      eps = Episode.objects.filter(show=show)
      for loc in Location.objects.filter(episode__in=eps).distinct():
        dir=os.path.join(self.show_dir,'dv',loc.slug)
        print show,loc,dir
        self.one_loc(loc, dir)

    def work(self):
        """
        find and process show
        """
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)

            self.show_dir = os.path.join(
                  self.options.mediadir,client.slug,show.slug)

            self.one_show(show)

        return

if __name__=='__main__': 
    p=add_dv()
    p.main()

