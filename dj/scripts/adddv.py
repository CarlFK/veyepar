#!/usr/bin/python

# Adds the .dv files to the raw files table

import  os

from process import process

from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class add_dv(process):

# Raw_File.objects.filter(location__show=show).delete()

    def one_dir(self, location, dir):
    
        files=os.listdir(dir)
        seq=0
        for dv in [f for f in files if f[-3:]=='.dv']:
            seq+=1
            # print dv
            pathname = os.path.join(dir,dv)
            print pathname
            rf, created = Raw_File.objects.get_or_create(
                location=location,
                filename=dv,)
            if created: 
                rf.sequence=seq
                rf.save()


    def one_loc(self,location,dir):
      files=os.listdir(dir)
      print files
      for dt in files:
        # dt is typicaly a date looking thing: 2009-08-20
        dir = os.path.join(dir,dt) 
        print (location,dir)
        self.one_dir(location,dir)

    def one_show(self, show):
      for loc in Location.objects.filter(show=show):
        dir=os.path.join(self.show_dir,'dv',loc.slug)
        print show,loc,dir
        self.one_loc(loc, dir)

if __name__=='__main__': 
    p=add_dv()
    p.main()

