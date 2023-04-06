#!/usr/bin/python

# Adds the media asset files to the Raw_Files table
# also adds the Cut Clicks to te Mark table

import  os
import datetime
from fnmatch import fnmatch

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Mark

VIDEO_EXTENSIONS = ('.dv', '.flv', '.mp4', '.MTS', '.mkv', '.mov', '.ts')

class add_dv(process):

    def mark_file(self,pathname,show,location):
        # one file of timestamps when Cut was Clicked
        fullpathname = os.path.join(
                self.show_dir, "dv", location.slug, pathname )

        with open(fullpathname) as f:
            cutlist = f.read().strip()
        if not cutlist:
            return

        for line in cutlist.split('\n'):
            if line:
                try:
                    click = datetime.datetime.strptime(
                            line,'%Y-%m-%d/%H_%M_%S')
                    # click = click + datetime.timedelta(hours=-1)
                except ValueError as e:
                    print(e)
                    continue

            print(click, end=' ')

            mark, created = Mark.objects.get_or_create(
                show=show, location=location,
                click=click)

            if created:
                print("(new)")
                mark.save()
            else:
                print(" {} (exists)".format(mark.id))

    def one_file(self,pathname,show,location,seq):
        # one video asset file
        print(pathname, end=' ')
        if self.options.test:
            rfs = Raw_File.objects.filter(
                show=show, location=location,
                filename=pathname,)
            if rfs: print("in db:", rfs)
            else: print("not in db")
        else:

            fullpathname = os.path.join(
                   self.show_dir, "dv", location.slug, pathname )
            st = os.stat(fullpathname)
            filesize=st.st_size

            if filesize == 0:
               print("(zero size)")

            else:

                rf, created = Raw_File.objects.get_or_create(
                    show=show, location=location,
                    filename=pathname,)

                if created:
                   print("(new)")
                   rf.sequence=seq
                   rf.filesize=filesize
                   rf.save()
                else:
                   print(f"(exists) {rf} {rf.id}")

    def one_loc(self,show,location):
        """
        finds dv files for this location
        """
        if self.options.whack:
            Raw_File.objects.filter(show=show).delete()
            Mark.objects.filter(show=show).delete()

        loc_dir=os.path.join(self.show_dir,'dv',location.slug)
        if self.options.verbose:  print("loc dir:", loc_dir)
        seq=0
        # os.walk returns a list of branches and leaves
        # branches are the dirs,
        #   leaves are the files at the end of each branch
        # the branch includes the root (which we don't want in the db)
        for dirpath, dirnames, filenames in os.walk(loc_dir,followlinks=True):
            # dirpath is the whole path from /
            # we want to strip off .../client/show/dv/loc
            # and only store what is under loc/
            stuby=dirpath[len(loc_dir)+1:]
            if self.options.verbose:
                print("checking...", dirpath, stuby, filenames)

            for filename in filenames:
                if self.options.verbose:
                    print("filename: {}".format(filename))

                if filename.startswith('.'):
                    # hidden file, skip it.
                    continue

                basename, extension = os.path.splitext(filename)

                # cut list file from voctomix
                if extension == ".log":
                    self.mark_file(
                            os.path.join(stuby,filename),show,location)
                    continue

                # skip Low Quality version made by sync-rax
                if basename in filenames:
                    # foo.ts makes foo.ts.mp4.
                    # strip the .mp4, see if foo.ts in [foo.ts]
                    # the mp4 is the lq from sync-rax, so don't add it.
                    if os.path.splitext(basename)[1] in VIDEO_EXTENSIONS:
                        # I am not sure how we got here if it wasn't an lq
                        # so I am not sure why we are checking this
                        # but tweed says:
                        # This must be a preview mp4 for web editing
                        if self.options.verbose:
                            print("skipping low quality")
                        continue

                pathname=os.path.join(dirpath,filename)
                if self.options.include and not fnmatch(
                        pathname,self.options.include):
                    # only add files that match --include
                    if self.options.verbose:
                        print("skipping (not in --include)")
                    continue

                if extension in VIDEO_EXTENSIONS:
                    seq+=1
                    self.one_file(
                        os.path.join(stuby,filename),show,location,seq)

    def one_show(self, show):
      if self.options.whack:
          Raw_File.objects.filter(show=show).delete()
      return super(add_dv, self).one_show(show)

    def work(self):
        """
        find and process show
        """
        if self.options.client:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(
                    client=client, slug=self.options.show)
        else:
            show = Show.objects.get(slug=self.options.show)

        self.one_show(show)

        return

    def add_more_options(self, parser):
        parser.add_option('--include',
           help="only include this glob.")

if __name__=='__main__':
    p=add_dv()
    p.main()

