#!/usr/bin/python

# adds episodes from an external source, like a csv

import datetime 
import process

from main.models import Client, Show, Location, Episode

class process_sched(process.process):
   
    state_done=2

    def one_show(self, show):
        sched = """09:30 Morning Tea available on arrival
10:00 ACQA - 'Yesterday, Today and Tomorrow '
10:45 Michael Peachy & Nick Heywood Wellness & Lifestyle
11:30 Nigel Langes - The 'Planting Seeds' Project; a mindset, a philosophy and a shared vision .
12:15 Lunch
13.00 ACQA AGM
13:15 Guest Speaker - Guild Insurance - 'Risk Management'
14:00 Caroline Lee - LeeCarePlus - 'Preparation for an interface with ACQA'
14:30 Kim Densham Rytec 'Computerised Rostering'
15:00 Chris McCann - TAFE '2010 - Aged Care Education Options'
15.30 Terry Wilby - Forum Close - ACQA Chairperson""" 
        eps=[]
        for row in sched.split('\n'):
            eps.append({'name':row[5:], 'start': \
                datetime.datetime(2009, 10, 2, int(row[0:2]), int(row[3:5]))})
        
# set the end times to the start of the next event.  close enough.
        for i in range(len(eps)-1):
            eps[i]['end']=eps[i+1]['start']
# "finishing at 15:45pm"
        eps[-1]['end']= datetime.datetime(2009, 10, 2, 15, 45)

        seq=0
        for row in eps:
            seq+=1

            room="Arkaba"   
            location,created = Location.objects.get_or_create(
                show=show,name=room,slug=process.fnify(room))

            ep = Episode(
               sequence=seq,
               location=location, 
               name=row['name'],
               slug=process.fnify(row['name']),
               start=row['start'], end=row['end'],
               state=self.state_done)
            if options.verbose:
                print ep.__dict__
            ep.save()

    def main(self):
      options, args = self.parse_args()

      if options.list:
          self.list()
      elif options.client and options.show:
        client,created = Client.objects.get_or_create(
            name=options.client, slug=options.client)
        show,created = Show.objects.get_or_create(client=client,
            name=options.show, slug=options.show)
        if options.verbose:
            print client, show
        if options.whack:
# clear out previous runs for this show
            Episode.objects.filter(location__show=show).delete()
            Location.objects.filter(show=show).delete()
        self.csv_pathname = options.filename
        self.one_show(show)

if __name__ == '__main__':
    p=process_sched()
    p.main()

