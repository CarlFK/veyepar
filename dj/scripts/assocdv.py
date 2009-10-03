#!/usr/bin/python

# creates cutlist items for dv files that might belong to an episode

import os

import process

from django.db.models import Q

# from main.models import Client, Show, Location, Episode, Raw_File, Cut_List

class ass_dv(process.process):

    def one_dv(self, dv, seq ):
        print dv, dv.location
        orph_name='orphans %s %s' % (
            dv.location.name,
            dv.start.strftime('%a_%d'),
            )
        orph_slug = process.fnify(orph_name)
        # find Episodes this may be a part of, add a cutlist record
        eps = Episode.objects.filter(
            Q(start__lte=dv.end)|Q(start__isnull=True), 
            Q(end__gte=dv.start)|Q(end__isnull=True), 
            location=dv.location).exclude(slug='orphans').exclude(slug=orph_slug )
        if not eps:
            # if no episodes found, attach to the orphan bucket
            dvdate=dv.start.date()  # date the clip started on 
            start = datetime.datetime.combine(dvdate,datetime.time(0))
            end = datetime.datetime.combine(dvdate,datetime.time(23,59,59))
            ep,created=Episode.objects.get_or_create(
               name=orph_name,slug=orph_slug,
               start=start, end=end,
               location=dv.location)
            eps=[ep]
        else: eps=[] # only add orphans now.  hack atack.

        for ep in eps:
            print ep
            cl, created = Cut_List.objects.get_or_create(
                episode=ep,
                raw_file=dv,
                sequence=seq)


    def one_loc(self,location):
      seq=0
      for dv in Raw_File.objects.filter(location=location).order_by('start'):
        seq+=1
        self.one_dv(dv,seq)

    def one_show(self, show):
      if self.options.whack:
          Cut_List.objects.filter(raw_file__location__show=show).delete()
          Cut_List.objects.filter(episode__location__show=show).delete()
          return

      for loc in Location.objects.filter(show=show):
        print show,loc
        self.one_loc(loc)

if __name__=='__main__': 
    p=ass_dv()
    p.main()

