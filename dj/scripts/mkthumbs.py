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
            dv.thumbnail = imgname
            dv.save()

        dv.ocrtext=ocrtext
        dv.save()
	return imgname

    def process_eps(self,episodes):
      for ep in episodes:
          print ep.location.slug
          dir=os.path.join(self.show_dir,'dv',ep.location.slug)
          dvs = Raw_File.objects.filter(cut_list__episode=ep)
          if dvs:
              for dv in dvs:
                  self.one_dv(dir,dv)
              if not ep.thumbnail:
                  ep.thumbnail = dvs[0].thumbnail
          

    def one_loc(self,location,dir):
      for dv in Raw_File.objects.filter(location=location):
        self.one_dv(dir,dv)

    def one_show(self, show):
      eps = Episode.objects.filter(show=show)
      for loc in Location.objects.filter(episode__in=eps):
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

