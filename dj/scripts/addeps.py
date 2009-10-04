#!/usr/bin/python

# adds episodes from an external source, like a csv

import datetime 
import urllib2,json
# from csv import DictReader
# from datetime import timedelta
from dateutil.parser import parse

import process

from main.models import Client, Show, Location, Episode

class process_csv(process.process):
   
    state_done=2

    def one_show(self, show):
      seq=1
      # j=urllib2.urlopen(
      #  'http://0.0.0.0:8080/main/C/DjangoCon/S/djc09.json').read()
      j = open('schedules/djangocon09.json').read()
      eps = l=json.loads(j)
      for ep in eps:
      # for row in DictReader(open(self.csv_pathname)):
        # print ep

        room=ep['location']
        # location,created = Location.objects.get_or_create(
        #    show=show,name=room,slug=process.fnify(room))
        
        location = Location.objects.get(show=show,name=room)
        
        name = ep['name']
        authors=ep['authors']
        primary=''
        start = parse(ep['start'])
        end = parse(ep['end'])

        episodes = Episode.objects.filter(name__iexact=name)
        print len(episodes),
        if not episodes: 
            print name
            ep = Episode(
               sequence=seq,
               location=location, 
               name=name,
               slug=process.fnify(name),
               primary=primary,
               authors=authors, 
               start=start, end=end,
               state=self.state_done)
            # print ep.__dict__
            # ep.save()
        seq+=1

    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="talks.csv",
          help='csv file' )

    def main(self):
      options, args = self.parse_args()

      if options.list:
          self.list()
      elif options.client and options.show:
        client,created = Client.objects.get_or_create(
            name=options.client, slug=options.client)
        show,created = Show.objects.get_or_create(client=client,
            name=options.show, slug=options.show)
        if options.whack:
# clear out previous runs for this show
            Episode.objects.filter(location__show=show).delete()
            Location.objects.filter(show=show).delete()
        self.csv_pathname = options.filename
        self.one_show(show)

if __name__ == '__main__':
    p=process_csv()
    p.main()

