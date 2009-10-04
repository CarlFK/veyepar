#!/usr/bin/python

# creates cutlist items for dv files that might belong to an episode

import os, datetime
import process
from main.models import Location, Episode, Raw_File, Cut_List

from django.db.models import Q

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
            location=dv.location)
        if not eps:
            # if no episodes found, it's an orphan
            # make a parent, 
            # calc the start/end to take up whatever gap is in the schedule

            # find the Episodes before and after it in the same location
            # if none found, use the start/end of the day as the boundry.

            dvdate=dv.start.date()  # date the clip started on 
            date_start = datetime.datetime.combine(dvdate,datetime.time(0))
            date_end = datetime.datetime.combine(dvdate,datetime.time(23,59,59))

            e=Episode.objects.filter( location=dv.location,
                start__range=(date_start,dv.start)).order_by('-start')
            if e: start = e[0].start
            else: start = date_start

            e=Episode.objects.filter( location=dv.location,
                end__range=(dv.end,date_end)).order_by('end')
            if e: end = e[0].end
            else: end = date_end

            ep,created=Episode.objects.get_or_create(
               name=orph_name,slug=orph_slug,
               start=start, end=end,
               location=dv.location)
            eps=[ep]

        for ep in eps:
            print ep
            cl, created = Cut_List.objects.get_or_create(
                episode=ep,
                raw_file=dv )
            if created:
                cl.sequence=seq
                cl.save()


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

