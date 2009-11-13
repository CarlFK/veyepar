#!/usr/bin/python

"""
mkthumbs.py - find thumbs
ocr untill we find some text
"""

import  os

import ocrdv

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class add_dv(process):

    def one_dv(self, dir, dv ):
        
        pathname = os.path.join(dir,dv.filename)
        print pathname

        ocrtext,img=ocrdv.ocrdv(pathname)

        if img:
            imgname = os.path.join(dir,dv.basename()+".png")
            img.save(imgname,'png')

        dv.ocrtext=ocrtext
        dv.save()

    def process_eps(self,episodes):
      for ep in episodes:
          show=ep.location.show
          client=show.client
          print ep.location.slug
          dir=os.path.join(self.show_dir,'dv',ep.location.slug)
          for dv in Raw_File.objects.filter(cut_list__episode=ep):
              self.one_dv(dir,dv)

    def one_loc(self,location,dir):
      for dv in Raw_File.objects.filter(location=location):
        self.one_dv(dir,dv)

    def one_show(self, show):
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

            self.show_dir = os.path.join(
                  self.options.mediadir,client.slug,show.slug)

            self.one_show(show)

        return

if __name__=='__main__': 
    p=add_dv()
    p.main()

