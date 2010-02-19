#!/usr/bin/python

# adds episodes from an external source, like a csv

import datetime 
import urllib2,json
# from csv import DictReader
# from datetime import timedelta
# from dateutil.parser import parse

import process

from main.models import fnify, Client, Show, Location, Episode

class process_csv(process.process):
   
    state_done=1

    def one_show(self, show):
      url='http://us.pycon.org/2010/conference/schedule/events.json'
      j=urllib2.urlopen(url).read()
      # j=open('events.json').read()
      d = json.loads(j)

      seq=0
      locs=d['rooms']
      for l_id in locs:
          l = locs[l_id]
          seq+=1
          name = l['name']
          slug=fnify(name)
          print name, slug
          loc,created = Location.objects.get_or_create(
              name=name, slug=slug)
          if created: 
              loc.sequence=seq
              loc.save()
          # save the loc object into the dict
          # so that it can be used for the FK object for episodes
          l['loc']=loc
          
      seq=0
      eps = d['events']
      for ep_id in eps:
        ep=eps[ep_id]
        seq+=1
        print ep

        room = ep['room']
        if room not in [ None, 'None' ]:
            location = locs[str(room)]['loc']
        else:
            location = None
        
        name = ep['title']
        slug=fnify(name)
        authors=ep['presenters']
        primary=str(ep['id'])
        start = datetime.datetime(*ep['start'])
        end = start + datetime.timedelta(minutes=ep['duration'])

        episode,created = Episode.objects.get_or_create(
            show=show,
            primary=primary)
        if created:
            episode.sequence=seq
        episode.location=location 
        episode.name=name
        episode.slug=fnify(name)
        episode.primary=primary
        episode.authors=authors
        episode.start=start
        episode.end=end
        episode.state=self.state_done
        episode.save()

    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="talks.csv",
          help='csv file' )

    def work(self):
      if self.options.client and self.options.show:
        client = Client.objects.get(slug=self.options.client)
        show = Show.objects.get(client=client,slug=self.options.show)
        
        if self.options.whack:
# clear out previous runs for this show
            Episode.objects.filter(show=show).delete()
            # Location.objects.filter(show=show).delete()
        self.one_show(show)

if __name__ == '__main__':
    p=process_csv()
    p.main()

