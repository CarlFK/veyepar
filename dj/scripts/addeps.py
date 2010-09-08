#!/usr/bin/python

# adds episodes from an external source, like a json file or url.

"""
fields:
Room Name 
Start - datetime 
Duration in minutes, or HH:MM:SS 
Title
Presenters - comma seperated list of people's names.
Description - used as the description of the video
ID of item in source database
URL of talk page
tags - comma seperated list 
"""

import datetime 
import urllib2,json
# from csv import DictReader
# from datetime import timedelta
# from dateutil.parser import parse

import process

from main.models import fnify, Client, Show, Location, Episode

class add_eps(process.process):

    def addlocs(self, schedule):
      """ pycon 2010 
      seq=0
      locs=d['rooms']
      for l_id in locs:
          l = locs[l_id]
          seq+=1
          name = l['name']
          slug=fnify(name)
          slug=slug.replace('_','')
          if slug in ["Centennial","Hanover F+G"]: 
              continue
          if slug =="RegencyV":
              slug="RegencyVI"
          if self.options.verbose: print name, slug
          if self.options.test:
              # hacked to verify database after cat made some changes.
              loc = Location.objects.get(
                  name=name, slug=slug)
          else:
              loc,created = Location.objects.get_or_create(
                  name=name, slug=slug)
              if created: 
                  loc.sequence=seq
                  loc.save()
          # save the loc object into the dict
          # so that it can be used for the FK object for episodes
          l['loc']=loc
       """
          
      seq=0
      for row in schedule:
          room = row['room']
          loc,created = Location.objects.get_or_create(name=room)
          if created: 
              seq+=1
              loc.sequence=seq
              loc.save()

  
    def addeps(self, schedule, show):
      seq=0

      for i in [1, 2, 10, 23, 14, 26, 27, 31, 32, ]:
        for row in schedule:
          if i == row['id']: print row
        print

      return
      for row in schedule:

          name = row['title']
          if name in ["Topics of Interest",
                "Why Django Sucks, and How We Can Fix It",
                "Technical Design Panel",
                "NoSQL and Django Panel",
                ]:
             room = 'Plenary'
          else:
             room = row['room']
          location = Location.objects.get(name=room)
          primary = row['url']
          # start=datetime.datetime.strptime(row['Start'],'%m/%d/%y %I:%M %p')
          start = datetime.datetime(*row['start'])
          start += datetime.timedelta(hours=-7,minutes=0)
          authors=row['presenters']
          minutes = row['duration']
          if not minutes: minutes = '50'
          # if minutes: duration = "00:%s:00" % minutes
          # else: duration = "01:00:00"
          # hours = int(int(minutes)/60)
          # minutes = int(minutes) % 60
          # duration="0%s:%s:00" % ( hours, minutes) 
          duration="00:%s:00" % ( minutes) 
          description = row['description']
          tags = row['tags']

          # print row
          if name in ['Registration','Lunch']:
              continue

          if name in ["Welcome and Chairman's Address",
                'Keynote', 'Lightning Talks', 'Sprints Kickoff']:
              primary=''
          
          if self.options.test:
              print location
              print name
              print primary
              print start
              print authors
              print duration
              print description
              print tags
              print
          else:
              episode,created = Episode.objects.get_or_create(
                  show=show, primary=primary)
              if created:
                  episode.sequence=seq
                  seq+=1
              episode.location=location 
              episode.name=name
              episode.primary=primary
              episode.authors=authors
              episode.start=start
              episode.duration=duration
              episode.description=description
              episode.state=1
              episode.save()


      """ pycon 2010
      seq=0
      eps = d['events']
      for ep_id in eps:
        ep=eps[ep_id]
        seq+=1
        if self.options.verbose: print ep

        room = ep['room']
        if room in [ None, 'None', '1' ]:
            room='1'
        #if room == '57': 
        #    room='47'
        
        print  str(room)
        print  locs[str(room)]
        location = locs[str(room)]['loc']
        
        name = ep['title']
        slug=fnify(name)
        authors=ep['presenters']
        primary=str(ep['id'])
        start = datetime.datetime(*ep['start'])
        end = start + datetime.timedelta(minutes=ep['duration'])
        print name
        print start
        print end
        print ep['duration']

        if self.options.test:
            episode = Episode.objects.get(
                show=show, primary=primary)
            if episode.location != location:
                print  episode.name, episode.location, location
                if self.options.force:
                    episode.location = location
                    episode.state = 2
                    episode.save()
        else:
            episode,created = Episode.objects.get_or_create(
                show=show, primary=primary)
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
       """



    def one_show(self, show):
      # url='http://us.pycon.org/2010/conference/schedule/events.json'
      # url='http://pycon-au.org/2010/conference/schedule/events.json'
      url='http://djangocon.us/schedule/json/'
      j=urllib2.urlopen(url).read()
      # j=open('schedule.json').read()
      schedule = json.loads(j)

      self.addlocs(schedule)
      self.addeps(schedule, show)

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
    p=add_eps()
    p.main()

