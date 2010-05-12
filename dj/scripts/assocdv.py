#!/usr/bin/python

# creates cutlist items for dv files that might belong to an episode

import os, datetime
import process
from main.models import Location, Episode, Raw_File, Cut_List, Client, Show

from django.db.models import Q

class ass_dv(process.process):

    def one_dv(self, dv, seq ):
        print dv, dv.location
        print dv.start, dv.end
        orph_name='orphans %s %s' % (
            dv.location.name,
            dv.start.strftime('%a_%d'),
            )
        orph_slug = process.fnify(orph_name)
        # find Episodes this may be a part of, add a cutlist record
        
        # for ep in Episode.objects.filter(location=dv.location):
        #    print ep.start, ep.end

        #    Q(end__gte=dv.start)|Q(end__isnull=True), 
        eps = Episode.objects.filter(
            Q(start__lte=dv.end)|Q(start__isnull=True),
            location=dv.location)
        
        for ep in eps:
            print ep
            
            # cls = Cut_List.objects.filter( episode=ep, raw_file=dv )
            # if len(cls)>1: print [c.id for c in cls]
            cl, created = Cut_List.objects.get_or_create(
                episode=ep,
                raw_file=dv )
            if created:
                cl.sequence=seq
                cl.save()

        print

    def one_loc(self,location):
      seq=0
      rfs=Raw_File.objects.filter(location=location).order_by('start')
      if self.options.day:
          rfs = rfs.filter(start__day=self.options.day)
      for dv in rfs:
        seq+=1
        self.one_dv(dv,seq)

    def one_show(self, show):
      if self.options.whack:
          Cut_List.objects.filter(raw_file__show=show).delete()
          Cut_List.objects.filter(episode__show=show).delete()
          return

      self.set_dirs(show)
      eps = Episode.objects.filter(show=show)
      for loc in Location.objects.filter(episode__in=eps).distinct():
        print show,loc
        self.one_loc(loc)

    def work(self):
        """
        find and process show
        """
        if self.options.client and self.options.show:
            client = Client.objects.get(slug=self.options.client)
            show = Show.objects.get(client=client, slug=self.options.show)
            self.one_show(show)

        return

if __name__=='__main__': 
    p=ass_dv()
    p.main()

