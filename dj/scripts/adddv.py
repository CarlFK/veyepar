#!/usr/bin/python

# Adds the media asset files to the Raw_Files table
# also adds the Cut Clicks to te Mark table

import  os
import datetime

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Mark

class add_dv(process):

    def mark_file(self,pathname,show,location):
        # one file of timestamps when Cut was Clicked
        fullpathname = os.path.join(
                self.show_dir, "dv", location.slug, pathname )

        for line in open(fullpathname).read().split('\n'):
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
                print("(exists)")

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
            rf, created = Raw_File.objects.get_or_create(
                show=show, location=location,
                filename=pathname,)
            
            if created: 
               print("(new)")
               rf.sequence=seq

               fullpathname = os.path.join(
                       self.show_dir, "dv", location.slug, pathname )
               st = os.stat(fullpathname)    
               rf.filesize=st.st_size

               rf.save()
            else:
               print("(exists)")
   
    def one_loc(self,show,location):
      """
      finds dv files for this location
      """
      if self.options.whack:
          Raw_File.objects.filter(show=show).delete()
          Mark.objects.filter(show=show).delete()

      ep_dir=os.path.join(self.show_dir,'dv',location.slug)
      if self.options.verbose:  print("episode dir:", ep_dir)
      seq=0
      for dirpath, dirnames, filenames in os.walk(ep_dir,followlinks=True):
          d=dirpath[len(ep_dir)+1:]
          if self.options.verbose: 
              print("checking...", dirpath, d, dirnames, filenames) 

          if self.options.subs:
              # subs holds a bit of the dirs we want,
              # like graphics,video,Camera,GFX
              if not self.options.subs in dirpath:
                  continue

          for f in filenames:

              if os.path.splitext(f)[1] == ".log":
                  self.mark_file(os.path.join(d,f),show,location)

              if os.path.splitext(f)[1] in [
                      '.dv', '.flv', '.mp4', '.MTS', '.mkv', '.mov', '.ts' ]:
                  seq+=1
                  self.one_file(os.path.join(d,f),show,location,seq)

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
        parser.add_option('--subs', 
           help="only include path that include string.")

if __name__=='__main__': 
    p=add_dv()
    p.main()

