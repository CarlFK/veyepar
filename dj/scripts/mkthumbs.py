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

        orctext,img=ocrdv.ocrdv(pathname)
        imgname = os.path.join(dir,dv.basename()+".png")
        img.save(imgname,'png')

        dv.save()

    def one_loc(self,location,dir):
      for dv in Raw_File.objects.filter(location=location):
        self.one_dv(dir,dv)

    def one_show(self, show):
      for loc in Location.objects.filter(show=show):
        dir=os.path.join(self.show_dir,'dv',loc.slug)
        print show,loc,dir
        self.one_loc(loc, dir)

if __name__=='__main__': 
    p=add_dv()
    p.main()

