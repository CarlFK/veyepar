#!/usr/bin/python

# adds episodes from an external source, like a json file or url.

"""
fields:
id - uniquie ID of item (used to update item if details change)
name - title of talk
room - "room1" if there is only one room.
start - datetime in some parsable format 
duration in minutes, or HH:MM:SS 
end - datetime in some parsable format 
authors - list of people's names.
contact - list of email(s) of presenters.
released - permission to release.
license - CC license (13 is safe)
description - used as the description of the video (paragraphs are fine)
conf_key - PK in source database - should be uniquie across this file
conf_url - URL of talk page
tags - comma seperated list - serch terms, including sub topics briefly discussed in your talk.
"""

"""
NOTE: In general it is better to build the export as simple as posible, 
even at the expense of deviatng from the above fields.  Exporting extra
fields is just fine.  They will be ignored, or maybe I will use them in 
a future version.

For fields yuou don't have, plug in a value.  If you don't have 'released'
give me a "Yes" and let the presenters know.

Given historic problems with end and duration, give me what you have and 
derive the other one if it isn't too much trouble.  
I'll use it to verify the transformations.  


"""

"""
datetime and json:
There is a issue here because json doesn't define a date format.  Do whatever makes the server side code smallest and easiest to code. easy to read data is good too.  

Here is PyCon 2010's impemtation:
datetime objects are represented as a time tuple of six elements:
    (year, month, day, hour, min, sec) 
        "start":      [2010, 2, 19, 9, 30, 0],
        "duration":   30, # in min
http://us.pycon.org/2010/conference/schedule/json/
Easy to code, kinda hard to read.
I parse it with 
          start = datetime.datetime(*row['start'])
good.

This is also good:
    json: Start: "2011-06-09 19:00:00"
    parser:  datetime.datetime.strptime( x, '%Y-%m-%d %H:%M:%S' )

OSDC2010: easy to read, harder to parse/assemble into start durration.
http://2010.osdc.com.au/program/json
# Day: "Tue 23 Nov"
# Time: "09:00 - 17:00"
but if that is how it is stored on the server, don't try to transform it.

Again, keep the server side code simple.
I can fix my consumer easier than I can get someone else's website updated.
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

# for google calandar:
# import pw 
# import lxml.etree

import process


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

    def snake_holes(self, schedule):
        # this is dumb.  
        # currently there is no support for multi rooms.
      rooms=[]
      for row in schedule:
          row = row['fields']
          # row=row['node']
          if self.options.verbose: print row
          room = row['location']
          if room not in rooms: rooms.append(room)
      return rooms

    def snake_bites(self, schedule, location):
        events=[]

        fields=('location','sequence','conf_key','target',
            'name','slug', 'authors','emails', 'description',
            'start','duration', 
            'released', 'license', 'conf_key', 'conf_url', 'tags')

        for row in schedule:
            pk = row['pk']
            row = row['fields']
            if self.options.verbose: print row
            event={}
            for f in fields:
                event[f] = row[f]
            
            # fields that don't flow thought json that nice.
            if not event['conf_key']: event['conf_key'] = pk
            event['location'] = location
            event['start'] = datetime.datetime.strptime(
                    row['start'], '%Y-%m-%d %H:%M:%S' )

            events.append(event)

        return events

    def zoo_events(self, schedule):
        events=[]
        for row in schedule:
            if self.options.verbose: print row
            event={}
            # event['id'] = row['Id']
            event['name'] = row['Title']
            event['room'] = row['Room Name']
            event['start'] = datetime.datetime.strptime(
                    row['Start'], '%Y-%m-%d %H:%M:%S' )
            event['duration'] = row['Duration']
            event['authors'] = row['Presenters']
            contacts = {"Massimo Di Pierro":"mdipierro@cs.depaul.edu", 
                    "Christopher Webber":"cwebber@dustycloud.org", 
                    "Carl Karsten":"carl@personnelware.com", 
                    "Brian Ray":"brianhray@gmail.com", 
                    "Bill Mania":"bill@manialabs.us", }
            authors=row.get('presenters','')
            # event['contact'] = ""
            event['emails'] = contacts.get(row['Presenters'], "" )
            # print event['authors'], event['contact'], contacts

            event['released'] = True
            event['license'] = 13
            event['description'] = row['Description']
            event['conf_key'] = row['Id']
            event['conf_url'] = row['URL']
            event['conf_url'] = row['URL'][-1]
            event['tags'] = ''

            events.append(event)

        return events

    def zoo_cages(self, schedule):
      rooms=[]
      for row in schedule:
          # row=row['node']
          if self.options.verbose: print row
          room = row['Room Name']
          if room not in rooms: rooms.append(room)
      return rooms

    def get_rooms(self, schedule, key):
      rooms=[]
      for row in schedule:
          if self.options.verbose: print row
          room = row[key]
          if room not in rooms: rooms.append(room)
      return rooms


    def symp_events(self, schedule ):
        events=[]

        for row in schedule:
            if self.options.verbose: print row
            event={}
            event['id'] = row['id']
            event['name'] = row['title']
            
            event['location'] = row['room']
            if event['location']=='Plenary': event['location'] = "Cartoon 1" 

            event['start'] = datetime.datetime.strptime(
                    row['start_iso'], '%Y-%m-%dT%H:%M:%S' )

            seconds=(row['duration'] -10) * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = row['authors']
            event['emails'] = row['contact']
            event['released'] = row['released']
            event['license'] = row['released'] or '13'
            event['description'] = row['description']
            event['conf_key'] = row['id']

            event['conf_url'] = row['url']
            if event['conf_url'] is None: event['conf_url'] = ""

            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = row

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
          # episode,created = Episode.objects.get_or_create(
          #        show=show, conf_key=row['conf_key'], )
          episodes = Episode.objects.filter(
                  show=show, conf_key=row['conf_key'], )

          # if created:
          if episodes:
              created = False
              episode = episodes[0]
          else:
              episodes = Episode.objects.create(
                  show=show, conf_key=row['conf_key'], )
              episode.sequence=seq
              episode.state=1
              seq+=1
              created = True

          fields=(
        'name', 'authors', 'emails', 'description',
        'start','duration', 
        'released', 'license', 
        'conf_url', 'tags')

          if created or self.options.update:
              print row['location']
              episode.location=Location.objects.get(name=row['location'])
              for f in fields:
                  setattr( episode, f, row[f] )
                  # print( f, row[f] )
              episode.save()
          else:
              # check for diffs
              # report if different
              diff_fields=[]
              for f in fields:
                  a1,a2 = getattr(episode,f), row[f]
                  if (a1 or a2) and (a1 != a2): 
                      diff_fields.append((f,a1,a2))
              if diff_fields:
                  print 'veyepar #id name: #%s %s' % (episode.id, episode.name)
                  for f,a1,a2 in diff_fields:
                      print 'veyepar %s: %s' % (f,a1)
                      print '  event %s: %s' % (f,a2)
                  print

    def pyohio(self, schedule, show):
        # importing from some other instance
        rooms = self.get_rooms(schedule,'room')
        rooms = [r for r in rooms if r != 'Plenary' ]
        # print rooms
        self.add_rooms(rooms,show)

        events = self.symp_events(schedule)
        # print events
        self.add_eps(events, show)
        return 



    def veyepar(self, schedule, show):
        # importing from some other instance
        rooms = self.snake_holes(schedule)
        # hack because the veyepar export doesn't give room name
        # will fix when I need to.
        # rooms = ['enova']
        self.add_rooms(rooms,show)

        events = self.snake_bites(schedule,rooms[0])
        self.add_eps(events, show)
        return 


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
        # url='http://lca2011.linux.org.au/programme/schedule/json'
        # url='http://2011.pyohio.org/programme/schedule/json'
        # url='http://pyohio.nextdayvideo.com/programme/schedule/json'
        # url='http://veyepar.nextdayvideo.com/main/C/jschi/S/june_2011.json'
        url='http://pyohio.org/schedule/json/'

        j=urllib2.urlopen(url).read()
        # file('chipy.json','w').write(j) 
        # j=file('pyohio.json').read()

        # cache for speedy development 
        # j=file('schedule_a.json').read()
        # j=file('schedule.json').read()

        schedule = json.loads(j)
        # schedule = json.read(j)

        # look at fingerprint of file, call appropiate parser
        # print j[:10]
        # print schedule[0]
        if j.startswith('[{"pk": '):
            # veyepar show export
            return self.veyepar(schedule,show)

        if j.startswith('[{"') and schedule[0].has_key('last_updated'):
            # [{"last_up
            # pyohio
            return self.pyohio(schedule,show)

        if isZoo:
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
      if self.options.client and self.options.show:

        client,created = Client.objects.get_or_create(slug=self.options.client)
        if created:
          client.name = self.options.client.capitalize()
          client.save()

        show,created = Show.objects.get_or_create(
                             client=client,slug=self.options.show)
        if created:
          show.name = self.options.show.capitalize()
          show.save()
        
        if self.options.whack:
            # DRAGONS!
            # clear out previous runs for this show

            client,created = Client.objects.get_or_create(slug=self.options.client)
            client.delete()
            # locs = Location.objects.all()
            # for loc in locs: loc.delete()

            Episode.objects.filter(show=show).delete()
            # Location.objects.filter(show=show).delete()

        self.one_show(show)

if __name__ == '__main__':
    p=add_eps()
    p.main()

