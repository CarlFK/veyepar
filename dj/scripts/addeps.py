#!/usr/bin/python

# adds episodes from an external source, like a json file or url.

"""
fields:
id - uniquie ID of item (used to update item if details change)
name - title of talk
room - "room1" if there is only one room.
start - datetime in some parsable format 
duration in minutes, or HH:MM:SS 
authors - comma seperated list of people's names.
contact - email(s) of presenters.
released - permission to release.
license - CC license (13 is safe)
description - used as the description of the video (paragraphs are fine)
conf_key - PK in source database - should be uniquie across this file
conf_url - URL of talk page
tags - comma seperated list 
"""

"""
NOTE: In general it is better to build the export as simple as posible, 
even at the expense of deviatng from the above fields.  Exporting extra
fields is just fine.  They will be ignored.
For instance, if you store start and end in the database but not duration, 
export end, I can can calculate duration.  
Given historic problems with duration, I woujldn't mind seeing both end 
and duration so that I can verify my transformations.  
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

Again, keep the server side code simple.
"""

# FireFox plugin to view .json data:
# https://addons.mozilla.org/en-US/firefox/addon/10869/

import datetime 
import urllib2,json
# from csv import DictReader
# from datetime import timedelta
from dateutil.parser import parse

import gdata.calendar.client
import gdata.calendar.service

import pw # for google calandar

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
          if self.options.verbose: print row
          room = row['room']
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

          # start=datetime.datetime.strptime(row['Start'], '%Y-%m-%d %H:%M:%S' )
          # start=datetime.datetime.strptime(row['Start'],'%m/%d/%y %I:%M %p')

          # pycon dates:
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

        if row['room']:
          # name = lxml.etree.fromstring('<foo>' + row['Title'] + '</foo>').text
          name = row['title'] 
          room = row['room']
          locations = Location.objects.filter(name=room)
          if locations: location=locations[0]
          else: continue
          conf_key = row['id']
          start = datetime.datetime(*row['start'])
          duration="00:%s:00" % row['duration']
          # start, duration = self.talk_time(row['Day'],row['Time'])
          authors=row.get('presenters','')
          released=row['released']
          license=row.get('license',"13")
          description = row['description']
          conf_key = row['conf_key']
          conf_url = row.get('conf_url', "" )

          # tags = row['Keywords']
          tags = None
          # print row
          if name in ['Registration','Lunch']:
              continue

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
                  episode.conf_url=conf_url
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

    def zoo_cages(self, schedule):
      rooms=[]
      for row in schedule:
          # row=row['node']
          if self.options.verbose: print row
          room = row['Room Name']
          if room not in rooms: rooms.append(room)
      return rooms

    def zoo_events(self, schedule):
        events=[]
        for row in schedule:
            if self.options.verbose: print row
            event={}
            event['id'] = row['Id']
            event['name'] = row['Title']
            event['room'] = row['Room Name']
            event['start'] = datetime.datetime.strptime(
                    row['Start'], '%Y-%m-%d %H:%M:%S' )
            event['duration'] = row['Duration']
            event['authors'] = row['Presenters']
            event['contact'] = ''
            event['released'] = True
            event['license'] = 13
            event['description'] = row['Description']
            event['conf_key'] = row['Id']
            event['conf_url'] = row['URL']
            event['tags'] = ''

            events.append(event)

        return events

    def add_rooms(self, rooms, show):
      seq=0
      for room in rooms:
          if self.options.verbose: print room
          loc,created = Location.objects.get_or_create(
                  name=room,)
          if created: 
              seq+=1
              loc.sequence=seq
              loc.save()
              show.locations.add(loc)
              show.save()
          
    def add_eps(self, episodes, show):
      seq=0
      for row in episodes:
          if self.options.verbose: print row
          episode,created = Episode.objects.get_or_create(
                  show=show, conf_key=row['conf_key'], )

          if created:
              episode.sequence=seq
              seq+=1
              episode.state=1

          fields = [ 'name', 'conf_url', 'conf_key', 
                  'released', 'start', 'duration', 'description',
                   'authors', 'contact', 'released', 'license',
                   'tags', ]

          if created or self.options.update:
              episode.location=Location.objects.get(name=row['room'])
              for f in fields:
                  setattr( episode, f, row[f] )
                  print( f, row[f] )
              episode.save()
          else:
              # check for diffs
              # report if different
              diff_fields=[]
              for f in fields:
                  print f
                  a1,a2 = episode.__getattribute__(f), locals()[f]
                  if a1 != a2: diff_fields.append((f,a1,a2))
              if diff_fields:
                  print 'veyepar #id name: #%s %s' % (episode.id, episode.name)
                  for f,a1,a2 in diff_fields:
                      print 'veyepar %s: %s' % (f,a1)
                      print '  event %s: %s' % (f,a2)
                  print


    def zoo(self, schedule, show):
        rooms = self.zoo_cages(schedule)
        self.add_rooms(rooms,show)

        events = self.zoo_events(schedule)
        self.add_eps(events, show)
        return 

    def one_show(self, show):
        # url='http://us.pycon.org/2010/conference/schedule/events.json'
        # url='http://pycon-au.org/2010/conference/schedule/events.json'
        # url='http://djangocon.us/schedule/json/'
        # url='http://2010.osdc.com.au/program/json'
        # url='http://conf.followtheflow.org/programme/schedule/json'
        # url='http://lca2011.linux.org.au/programme/schedule/json'
        # url='http://veyepar.nextdayvideo.com/main/C/chipy/S/may_2011.json'
        url='http://lca2011.linux.org.au/programme/schedule/json'
        url='http://2011.pyohio.org/programme/schedule/json'

        j=urllib2.urlopen(url).read()
        file('chipy.json','w').write(j) 
        j=file('chipy.json').read()

        # j=file('schedule_a.json').read()
        # j=file('schedule.json').read()

        # j=open('schedule.json').read()
        schedule = json.loads(j)

        return self.zoo(schedule,show)

        # schedule = schedule['nodes']
        self.addlocs(schedule,show)
        self.addeps(schedule, show)
        return

        loc,created = Location.objects.get_or_create( 
                sequence = 1,
                name='Illinois Room A', slug='room_a' )
        if created: show.locations.add(loc)

        loc,created = Location.objects.get_or_create( 
                sequence = 2,
                name='Illinois Room B', slug='room_b' )
        if created: show.locations.add(loc)

        client = gdata.calendar.service.CalendarService()
        client.ClientLogin(pw.goocal_email, pw.goocal_password, client.source)
        fcal = client.GetAllCalendarsFeed().entry[7]
        print "fcal title:", fcal.title.text
        a_link = fcal.GetAlternateLink()
        feed = client.GetCalendarEventFeed(a_link.href)
        seq=0
        for event in feed.entry:

            name = event.title.text + 's talk'
            authors = event.title.text

            wheres = event.where
            room = wheres[0].value_string
            location = Location.objects.get(name=room)

            goo_start = event.when[0].start_time 
            goo_end = event.when[0].end_time

            print goo_start
            start = datetime.datetime.strptime(goo_start,'%Y-%m-%dT%H:%M:%S.000-05:00')
            end = datetime.datetime.strptime(goo_end,'%Y-%m-%dT%H:%M:%S.000-05:00')


            delta = end - start
            minutes = delta.seconds/60 # - 5 for talk slot that includes break
            hours = minutes/60
            minutes -= hours*60

            duration="%s:%s:00" % ( hours,minutes) 
            released = True

            # print name, authors, location, start, duration
            print "%s: %s - %s" % ( authors, location, start.time() )

            seq+=1
            episode,created = Episode.objects.get_or_create(
                  show=show, 
                  location=location,
                  start=start,
                  authors=authors)

            if created:
                  episode.name=name
                  episode.released=released
                  episode.start=start
                  episode.duration=duration
                  episode.sequence=seq
                  episode.state=1
                  episode.save()
             
        return 
        
    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="talks.csv",
          help='csv file' )
        parser.add_option('-u', '--update', action="store_true", 
          help='update when diff, else print' )

    def work(self):

      client,created = Client.objects.get_or_create(slug=self.options.client)
      client.delete()
      locs = Location.objects.all()
      for loc in locs: loc.delete()

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

