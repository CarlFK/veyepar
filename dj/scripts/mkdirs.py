#!/usr/bin/python

# Makes the dir tree to put files into

import  os,sys

from process import process

from main.models import Client, Show, Location

class mkdirs(process):

  def mkdir(self,dir):
      """ makes the dir if it doesn't exist """
      print dir,
      if os.path.exists(dir):
         print '(exists)'
      else:
         os.makedirs(dir)
         print

  def work(self):
        """
        find or create a client and show and the dirs
        """
        client = Client.objects.get(slug=self.options.client)
        show = Show.objects.get(client=client,slug=self.options.show)
        self.show_dir = os.path.join(
            self.options.mediadir,client.slug,show.slug)

        for d in "dv tmp/dv tmp/bling bling ogg ogv mp4 flv txt".split():
            self.mkdir(os.path.join(self.show_dir,d))

        for loc in Location.objects.filter(show=show):
             dir = os.path.join(self.show_dir,'dv',loc.slug)
             self.mkdir(dir)

        return

if __name__=='__main__': 
    p=mkdirs()
    p.main()

