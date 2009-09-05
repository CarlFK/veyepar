#!/usr/bin/python

# Makes the dir tree to put files into

import  os,sys

from process import process

from main.models import Client, Show, Location

class mkdirs(process):

  def mkdir(self,dir):
      """ makes the dir if it doesn't exist """
      print dir
      if not os.path.exists(dir):
         os.makedirs(dir)

  def one_show(self,show):
    self.mkdir(os.path.join(self.show_dir,'dv'))
    self.mkdir(os.path.join(self.show_dir,'ogg'))
    for loc in Location.objects.filter(show=show):
         dir = os.path.join(self.show_dir,'dv',loc.slug)
         self.mkdir(dir)

if __name__=='__main__': 
    p=mkdirs()
    p.main()

