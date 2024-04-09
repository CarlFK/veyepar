#!/usr/bin/python

# Makes the dir tree to put files into

import os,sys

from process import process

from main.models import Client, Show, Location, Episode

class mkdirs(process):

  def mkdir(self, *path_parts):
      # makes dir(s) if they doen't exist
      # path_parts: list of dir names: foo,bar,bas = foo/bar/baz/
      # mkdir foo
      # mkdir foo/bar
      # mkdir foo/bar/baz
      ret = False

      if self.options.rsync:
          # try to make dirs on the remote box
          print(path_parts)

          client = Client.objects.get(slug=self.options.client)
          show = Show.objects.get(client=client,slug=self.options.show)
          # remote_show_dir = os.path.join(self.options.media_dir, client.slug, show.slug)

          tail=""
          for part in path_parts:
              tail = os.path.join(tail, part)
              self.dir2cdn(show, tail)

      else:
          full_dir = os.path.join(self.show_dir, *path_parts)
          if os.path.exists(full_dir):
             print('(exists)')
          else:
             os.makedirs(full_dir)
             ret = True

      return ret


  def work(self):
        """
        find client and show, create the dirs
        """
        client = Client.objects.get(slug=self.options.client)
        show = Show.objects.get(client=client,slug=self.options.show)
        self.set_dirs(show)

        # create show dir root
        ret = self.mkdir("")

        dirs = "dv assets tmp titles webm mp4 mlt custom custom/titles img"
        for d in dirs.split():
            ret = self.mkdir(d)

        dirs = "credits mlt titles"
        for d in dirs.split():
            # full_dir = os.path.join(self.show_dir, "assets", d)
            # ret = self.mkdir(self.show_dir, "assets", d)
            ret = self.mkdir("assets", d)

        if self.options.rsync:
            return

        # copy the footer image
        # not sure where this should happen *shrug*
        # It's really just for the default,
        # If there is a non default, it will live under show_dir/assets/.
        # /home/carl/src/veyepar/dj/scripts/assets/credits/ndv/ndv-169.png

        credits_img = client.credits
        if credits_img == "ndv-169.png":
            credits_src = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "assets/credits/ndv",
                credits_img)
            # copy into show/assetts
            credits_pathname = os.path.join(
                    self.show_dir, "assets", "credits", credits_img )
            ret = self.run_cmd( ["cp", credits_src, credits_pathname] )

        # assets/titles/title.svg
        # Videos/veyepar/koya_law/training/assets/titles/

        fname = client.title_svg
        print("title_svg {}".format(fname))
        dst = os.path.join(
                self.show_dir, "assets", "titles", fname )
        print("dst {}".format(dst))
        if not os.path.exists(dst):
            # copy into show/assetts
            src = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "assets", "titles",
                "title.svg")
            print("src {}".format(src))
            self.run_cmd( ["cp", src, dst] )

        # src/veyepar/dj/scripts/assets/mlt/template.mlt
        # Videos/veyepar/koya_law/training/assets/mlt

        fname = client.template_mlt
        dst = os.path.join(
                self.show_dir, "assets", "mlt", fname )
        if not os.path.exists(dst):
        # copy into show/assetts
            src = os.path.join(
                os.path.split(os.path.abspath(__file__))[0],
                "assets", "mlt",
                "template.mlt")
            ret = self.run_cmd( ["cp", src, dst] )

        if self.options.raw_slugs:
            # I wonder what this is for?
            # help="Make a dir for each talk's raw files")

            # get episodes for this show
            eps = Episode.objects.filter(show=show)
            for ep in eps:
                loc = ep.location.slug
                dt = ep.start.strftime("%Y-%m-%d")
                slug = ep.slug
                ret = self.mkdir(self.show_dir,'dv',loc,dt,slug)

        else:

            # get locations of the episodes
            for loc in Location.objects.filter(
                    show=show, active=True):
                 ret = self.mkdir(self.show_dir,'dv',loc.slug)

        return

  def add_more_options(self, parser):
      parser.add_option('--raw-slugs', action="store_true",
                          help="Make a dir for each talk's raw files")
      parser.add_option('--rsync', action="store_true",
                          help="mkdirs on CDN")

if __name__=='__main__':
    p=mkdirs()
    p.main()

