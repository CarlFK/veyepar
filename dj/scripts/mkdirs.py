#!/usr/bin/python

# Makes the dir tree to put files into

import  os,sys

from process import process

from main.models import Client, Show, Location, Episode

class mkdirs(process):

  def mkdir(self,dir):
      """ makes the dir if it doesn't exist """
      ret = False
      print dir,
      if os.path.exists(dir):
         print '(exists)'
      else:
         if self.options.test:
             print '(testing, skipped)'
         else:
             os.makedirs(dir)
             ret = True
         print

      return ret

  def work(self):
        """
        find client and show, create the dirs
        """
        client = Client.objects.get(slug=self.options.client)
        show = Show.objects.get(client=client,slug=self.options.show)
        self.set_dirs(show)
        dirs = "dv assets tmp titles webm mp4 mlt custom/titles"
        for d in dirs.split():
            full_dir = os.path.join(self.show_dir,d)
            ret = self.mkdir(full_dir)

        # copy the footer image 
        # not sure where this should happen *shrug*
        # It's really just for the default, 
        # If there is a non default, it will live under show_dir/assets/.

        credits_img = client.credits
        credits_src = os.path.join(
            os.path.split(os.path.abspath(__file__))[0],
            "bling",
            credits_img)
        # copy into show/assetts
        credits_pathname = os.path.join(
                self.show_dir, "assets", credits_img )

        self.run_cmd( ["cp", credits_src, credits_pathname] )

        if self.options.raw_slugs:

        # get episodes for this show
            eps = Episode.objects.filter(show=show)
            for ep in eps:
                loc = ep.location.slug
                dt = ep.start.strftime("%Y-%m-%d")
                slug = ep.slug
                full_dir = os.path.join(self.show_dir,'dv',loc,dt,slug)
                ret = self.mkdir(full_dir)

        else:

    # get locations of the episodes
            for loc in Location.objects.filter(
                    show=show, active=True):
                 dir = os.path.join(self.show_dir,'dv',loc.slug)
                 ret = self.mkdir(dir)

        return

  def add_more_options(self, parser):
      parser.add_option('--raw-slugs', action="store_true",
                          help="Make a dir for each talk's raw files")

if __name__=='__main__': 
    p=mkdirs()
    p.main()

