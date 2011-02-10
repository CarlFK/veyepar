#!/usr/bin/python

# adds episodes from an external source, like a json file or url.

"""
fields:
id - uniquie ID of item (used to update item if details change)
ritle - of talk
room - "room1" if there is only one room.
start - datetime in some parsable format 
duration in minutes, or HH:MM:SS 
presenters - comma seperated list of people's names.
released - permission to release.
license - CC license (13 is safe)
description - used as the description of the video (paragraphs are fine)
conf_key - PK in source database - should be uniquie across this file
conf_url - URL of talk page
tags - comma seperated list 
"""

"""
There is a datetime format issue here because json doesn't define a date format.  Do whatever makes the server side code smallest and easiest to code. easy to read data is good too.  Do not write extra server side code to try and make it easier to parse.  That has lead to data loss, which means trying to debug a ssytem that starts with the event's data input and ends with veyepar's database, which is not fun.  

Here is PyCon 2010's impemtation:
datetime objects are represented as a time tuple of six elements:
    (year, month, day, hour, min, sec) 
        "start":      [2010, 2, 19, 9, 30, 0],
        "duration":   30, # in min
http://us.pycon.org/2010/conference/schedule/json/
Easy to code, hard to read.

OSDC2010: easy to read, harder to parse/assemble into start durration.
http://2010.osdc.com.au/program/json
# Day: "Tue 23 Nov"
# Time: "09:00 - 17:00"
"""

# FireFox plugin to view .json data:
# https://addons.mozilla.org/en-US/firefox/addon/10869/

import datetime 
import urllib2,json
# from csv import DictReader
# from datetime import timedelta
from dateutil.parser import parse

import process
import lxml.etree


from main.models import fnify, Client, Show, Location, Episode

class add_eps(process.process):

    def addlocs(self, schedule, show):
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
          # row=row['node']
          room = row['Room Name']
          if room in [
             '',
             "Napalese Pagoda",
             "Z4 Atrium",
             "Maritime Museum",
             "Grand Hall - BCEC",
             ]: continue
          loc,created = Location.objects.get_or_create(name=room)
          if created: 
              seq+=1
              loc.sequence=seq
              loc.save()
              show.locations.add(loc)
              show.save()
          else:
            print row

    def  talk_time(self, day,time):
# Day: "Wed 24 Nov"
# Time: "09:00 - 10:00"
        start_ts, end_ts = time.split('-')

        start_dts = day + ' 2010 ' + start_ts
        end_dts = day + ' 2010 ' + end_ts

        start_dt = parse(start_dts)        
        end_dt = parse(end_dts)        

        delta = end_dt - start_dt
        minutes = delta.seconds/60 # - 5 for talk slot that includes break

        duration="00:%s:00" % ( minutes) 
        return start_dt, duration

          # start=datetime.datetime.strptime(row['Start'],'%m/%d/%y %I:%M %p')

          # [ 2010, 9, 7, 15, 0 ]
          # start = datetime.datetime(*row['start'])


          # minutes = row['duration']

          # adjust for time zone:
	  # start += datetime.timedelta(hours=-7,minutes=0)


    def addeps(self, schedule, show):
      seq=0

      for row in schedule:

        # row = row['node']
        if self.options.verbose: print row
        if row['Title'] in [
            'Registration',
            'Welcome to linux.conf.au 2011!',
            'Morning Tea', 'Afternoon Tea',
            "Speaker's Dinner",
          ]:
           continue
        if row['Room Name']:
          # name = lxml.etree.fromstring('<foo>' + row['Title'] + '</foo>').text
          name = row['Title'] 
          room = row['Room Name']
          locations = Location.objects.filter(name=room)
          if locations: location=locations[0]
          else: continue
          conf_key = row['Id']
          start=datetime.datetime.strptime(row['Start'], '%Y-%m-%d %H:%M:%S' )
          duration = row['Duration']
          # start, duration = self.talk_time(row['Day'],row['Time'])
          authors=row.get('Presenters','')
          released=row['released']
          # released=None
          license=row['license']
          # url = row['Link']
          description = row['Description']
          if description:
              url = \
                "http://conf.linux.org.au/programme/schedule/view_talk/%s" \
                 % (row['Id'])
          else:
              url = "http://conf.linux.org.au"
          # never mind all that URL stuff.  this is simpler:
          url = row.get('URL', "http://conf.linux.org.au" )

          # tags = row['Keywords']
          tags = None
          # print row
          if name in ['Registration','Lunch']:
              continue

          if name in ["Welcome and Chairman's Address",
                'Keynote', 
                'Lightning Talks', 
                'Distinguished Guest Speaker', 
                'Sprints Kickoff']:
              conf_key=''
          
          if self.options.test:
              print location
              print name
              print conf_key
              print start
              print authors
              print duration
              print description
              print tags
              print
          else:
              episode,created = Episode.objects.get_or_create(
                  show=show, conf_key=conf_key, )

              if created:
                  episode.sequence=seq
                  seq+=1
                  episode.state=1

              if created or self.options.update:
                  episode.location=location 
                  episode.name=name
                  episode.conf_key=conf_key
                  episode.conf_url=url
                  episode.authors=authors
                  episode.released=released
                  episode.start=start
                  episode.duration=duration
                  episode.description=description
                  episode.save()
              else:
                  # check for diffs
                  # report if different
                  fields = [ 'location', 'name', 'conf_key', 'authors', 
                      'released', 'start', 'duration', 'description',]
                  diff_fields=[]
                  for f in fields:
                      a1,a2 = episode.__getattribute__(f), locals()[f]
                      if a1 != a2: diff_fields.append((f,a1,a2))
                  if diff_fields:
                      print 'veyepar #id name: #%s %s' % (episode.id, episode.name)
                      for f,a1,a2 in diff_fields:
                          print 'veyepar %s: %s' % (f,a1)
                          print '  event %s: %s' % (f,a2)
                      print


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
        conf_key=str(ep['id'])
        start = datetime.datetime(*ep['start'])
        end = start + datetime.timedelta(minutes=ep['duration'])
        print name
        print start
        print end
        print ep['duration']

        if self.options.test:
            episode = Episode.objects.get(
                show=show, conf_key=conf_key)
            if episode.location != location:
                print  episode.name, episode.location, location
                if self.options.force:
                    episode.location = location
                    episode.state = 2
                    episode.save()
        else:
            episode,created = Episode.objects.get_or_create(
                show=show, conf_key=conf_key)
            if created:
                episode.sequence=seq
            episode.location=location 
            episode.name=name
            episode.slug=fnify(name)
            episode.conf_key=conf_key
            episode.authors=authors
            episode.start=start
            episode.end=end
            episode.state=self.state_done
            episode.save()
       """



    def one_show(self, show):
      # url='http://us.pycon.org/2010/conference/schedule/events.json'
      # url='http://pycon-au.org/2010/conference/schedule/events.json'
      # url='http://djangocon.us/schedule/json/'
      # url='http://2010.osdc.com.au/program/json'
      url='http://conf.followtheflow.org/programme/schedule/json'
      j=urllib2.urlopen(url).read()
      file('lca.json','w').write(j) 
      j=file('lca.json').read()

      # j=open('schedule.json').read()
      schedule = json.loads(j)

      # schedule = schedule['nodes']
      self.addlocs(schedule,show)
      self.addeps(schedule, show)

    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="talks.csv",
          help='csv file' )
        parser.add_option('-u', '--update', action="store_true", 
          help='update when diff, else print' )

    def work(self):
      if self.options.client and self.options.show:

        client,created = Client.objects.get_or_create(slug=self.options.client)
        if created:
          client.name = self.options.client
          client.save()

        show,created = Show.objects.get_or_create(
                             client=client,slug=self.options.show)
        if created:
          show.name = self.options.show
          show.save()
        
        if self.options.whack:
# clear out previous runs for this show
            Episode.objects.filter(show=show).delete()
            # Location.objects.filter(show=show).delete()
        self.one_show(show)

if __name__ == '__main__':
    p=add_eps()
    p.main()

