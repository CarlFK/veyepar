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
        
        dv_pathname = os.path.join(dir,dv.filename)
        png_pathname = os.path.join(dir,"%s.png"%dv.basename())
        print "dv:", dv_pathname
        print "png:", png_pathname

        if not os.path.exists(png_pathname):
            p=gsocr.Main(dv_pathname)
            gsocr.gtk.main()
            if p.words:
                dv.ocrtext=p.words
                # dv.thumbnail=p.imgname
                dv.save()
	    return p.basename
        return None

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
      self.set_dirs(show)
      for loc in Location.objects.filter(show=show):
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
            self.one_show(show)

        return

if __name__=='__main__': 
    p=add_dv()
    p.main()

