#!/usr/bin/python

# adds episodes from an external source, like a json file or url.

"""
fields:
name - title of talk
room - "room1" if there is only one room.
start - datetime in some parsable format 
duration in minutes
end - datetime in some parsable format 
authors - list of people's names.
contact - list of email(s) of presenters.
released - permission to release.
license - CC license 
description - used as the description of the video (paragraphs are fine)
conf_key - PK in source database - uniquie used to update this item 
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
import urllib2,csv
import HTMLParser
# from dateutil.parser import parse
# import pprint

try:
    import simplejson as json
except ImportError:
    import json

# import gdata.calendar.client
# import gdata.calendar.service

# for google calandar:
# import pw 
# import lxml.etree

import process


from main.models import fnify, Client, Show, Location, Episode, Raw_File

def goog(show,url):
    # read from goog spreadsheet api

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


    def str2bool(self, tf):
        return {'true':True, 
                "false":False}[tf]

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
          license=row['license']
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
        # importing from veyepar 
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

        # warning: location is the 2nd half of a hack:
        # veyepar json export only gives room key, not name
        # so convert the int to a string and call it the name.
        # lame.

        events=[]

        fields=('location','sequence','conf_key','host_url',
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
            # event['location'] = location
            event['start'] = datetime.datetime.strptime(
                    row['start'], '%Y-%m-%d %H:%M:%S' )

            events.append(event)

        return events

    def zoo_events(self, schedule):
        events=[]
        for row in schedule:
            if self.options.verbose: print row
            if row['Title'] in [
                'Registration', 
                'Morning Tea', "Lunch", 'Afternoon Tea',
                'Speakers Dinner', 'Penguin Dinner',
                'Professional Delegates Networking Session',
                # 'Sysadmin Miniconf'
                ]:  
                continue
            if "AGM" in row['Title']:
                continue
            # if "Lightning talks" in row['Title']:
            #     continue
            # if "Conference Close" in row['Title']:
            #    continue

            event={}
            event['name'] = row['Title']
            event['location'] = row['Room Name']
            event['start'] = datetime.datetime.strptime(
                    row['Start'], '%Y-%m-%d %H:%M:%S' )
            event['duration'] = row['Duration']
            event['authors'] = row.get('Presenters','')

            # https://github.com/zookeepr/zookeepr/issues/92
            event['emails'] = row.get('Presenter_emails','')

            # https://github.com/zookeepr/zookeepr/issues/93
            event['released'] = True

            event['license'] = self.options.license
            event['description'] = row['Description']
            # from /zookeepr/controllers/schedule.py
            # row['Id'] = schedule.id
            # row['Event'] = schedule.event_id
            # I think Id is what is useful
            event['conf_key'] = row['Id']

            # there may not be a URL, like for Lunch and Keynote.
            # https://github.com/zookeepr/zookeepr/issues/91
            event['conf_url'] = row.get('URL','')

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
          # if room is None: room = "Plenary"
          if room == "Plenary": 
              room = "Track I (D5)"
              row['room_name'] = "Mission City Ballroom"
          # room = "%s - %s" % ( row['room_name'], room )
          if room not in rooms: 
              rooms.append(room)
              # print room, '-',row['room_name']
      return rooms


    def symp_events(self, schedule ):
        events=[]

        for row in schedule:
            if self.options.verbose: print row
            event={}
            event['id'] = row['id']
            event['name'] = row['title']
            
            # event['location'] = row['room']
            # if event['location']=='Plenary': event['location'] = "Cartoon 1" 
            # if event['location'] is None: event['location'] = "Track 1" 
            # if event['location']=='Plenary': event['location'] = "Track 1" 
            if row['room'] == "Plenary": 
              row['room'] = "Track I (D5)"
              row['room_name'] = "Mission City Ballroom"
            # event['location'] = "%s - %s" % ( 
            #        row['room_name'], row['room'] )
            event['location'] = row['room']

            event['start'] = datetime.datetime.strptime(
                    row['start_iso'], '%Y-%m-%dT%H:%M:%S' )

            # if "Poster" in row["tags"]:
            event['start'] += datetime.timedelta(hours=-3)

            break_min = 0 ## no time for breaks!
            seconds=(row['duration'] - break_min ) * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = row['authors']
            event['emails'] = row['contact']
            event['released'] = row['released']
            event['license'] = row['license'] 
            event['description'] = row['description']
            event['conf_key'] = row['id']

            event['conf_url'] = row['url']
            if event['conf_url'] is None: event['conf_url'] = ""

            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = row

            events.append(event)

        return events

    def ddu_events(self, schedule ):
        # Drupal Down Under 2012

        html_parser = HTMLParser.HTMLParser()

        # these fields exist in both json and veyepar:
        common_fields = [ 'name', 'authors', 'description', 
            'start', 'duration', 
            'released', 'license', 'tags', 'conf_key', 'conf_url']

        # mapping of json to veyepar:
        field_map = [ 
                ('emails','contact'), 
                ('location','room'),
                ]
     
        html_encoded_fields = [ 'name', 'authors', 'description', ]

        events=[]
        for row in schedule:
            if self.options.verbose: print row
            event={}

            for k in common_fields:
                try: 
                    event[k] = row[k]
                except KeyError:
                    event[k] = 'missing'

            for k1,k2 in field_map:
                event[k1] = row[k2]

            if isinstance(event['authors'],dict):
                event['authors'] = ", ".join( event['authors'].values() )
            
            if row["entities"] == "true":
                for k in html_encoded_fields:
                    # x = html_parser.unescape('&pound;682m')
                    event[k] = html_parser.unescape( event[k] )

            
            # x = html_parser.unescape('&pound;682m')

            event['start'] = datetime.datetime.strptime(
                    event['start'], '%Y-%m-%d %H:%M:%S' )

            seconds=(int(event['duration'] )) * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['released'] = event['released'].startswith(
                "You may publish" )

            event['license'] = event['license'].split('(')[1][5:-1]

            event['emails']=None

            # save the original row so that we can sanity check end time.
            event['raw'] = row

            events.append(event)

        return events



    def goth_events(self, schedule ):
        # PyGotham

        # ['outline', 'title', 'room_number', 'duration_minutes', 'talktype', 'levels', 'full_name', 'talk_end_time', 'talk_day_time', 'desc']

        events=[]

        for pk,row in enumerate(schedule):
            if self.options.verbose: print pk, row
            event={}
            # event['id'] = row['id']
            event['id'] = row['key']
            event['name'] = row['title']
            
            event['location'] = row['room_number']

            event['start'] = datetime.datetime.strptime(
                    row['talk_day_time'], '%Y-%m-%d %H:%M:%S' )

            seconds=(row['duration_minutes'] -10) * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = row['full_name']
            event['emails'] = '' # row['contact']
            event['released'] = False
            event['license'] = ''
            event['description'] = row['desc']
            event['conf_key'] = row['key']

            event['conf_url'] = ''

            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = row

            events.append(event)

        return events

    def pct_events(self, schedule):
        # pyCon Tech
        # >>> schedule['events']['28'].keys()
        # [u'files', u'room', u'videos', u'title', u'url', u'id', u'tags', u'shorturl', u' sponsors', u'summary', u'presenters', u'duration', u'level', u'type', u'start']

        events=[]
        for event_id in schedule['events']:
          src_event=schedule['events'][event_id]
          if self.options.verbose: print src_event
          if src_event['type'] != 'Social Event':
            event={}
            # event['id'] = event_id
            event['name'] = src_event['title']
            event['location'] = schedule['rooms'][src_event['room']]['name']

            event['start'] = datetime.datetime(*src_event['start'])

            seconds=src_event['duration'] * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = src_event['presenters']
            event['emails'] = ''
            event['released'] = True
            event['license'] = self.options.license
            event['description'] = src_event['summary']
            event['conf_key'] = src_event['id']

            event['conf_url'] = src_event['url']
            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = src_event

            events.append(event)
 
        return events


    def add_rooms(self, rooms, show):
      seq=0
      for room in rooms:
          if self.options.verbose: print room
          loc,created = Location.objects.get_or_create(
                  name=room,)
          loc.active = False
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
              episode = Episode.objects.create(
                  show=show, conf_key=row['conf_key'], 
                  start=row['start'], duration=row['duration'],
                  )
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
              loc=Location.objects.get(name=row['location'])
              loc.active = True
              episode.location=loc
              for f in fields:
                  setattr( episode, f, row[f] )
                  # print( f, row[f] )
              episode.save()
              loc.save()
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


    def pctech(self, schedule, show):
        # importing from some other instance
        rooms = [schedule['rooms'][r]['name'] for r in schedule['rooms']]
        self.add_rooms(rooms,show)

        events = self.pct_events(schedule)
        self.add_eps(events, show)
        return 

    def pyohio(self, schedule, show):
        # print "consumer PyOhio"
        rooms = self.get_rooms(schedule,'room')
        rooms = [r for r in rooms if r != 'Plenary' ]
        self.add_rooms(rooms,show)

        events = self.symp_events(schedule)
        self.add_eps(events, show)
        return 

    def symposium(self, schedule, show):
        # print "consumer symposium"
        rooms = self.get_rooms(schedule,'room')
        # self.add_rooms(rooms,show)

        events = self.symp_events(schedule)
        self.add_eps(events, show)
        return 



    def pyconde2011(self, schedule, show):
        # importing from some other instance
        rooms = self.get_rooms(schedule,'room')
        rooms = [r for r in rooms if r != 'Plenary' ]
        self.add_rooms(rooms,show)

        events = self.symp_events(schedule)
        for e in events:
            print e
            end  = datetime.datetime.strptime(
                    e['raw']['end_iso'], '%Y-%m-%dT%H:%M:%S' )
            td = end - e['start']

            seconds=td.seconds
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            e['duration'] =  duration

        self.add_eps(events, show)
        return 


    def pygotham(self, schedule, show):
        # pygotham 2011
        rooms = self.get_rooms(schedule,'room_number')
        self.add_rooms(rooms,show)

        events = self.goth_events(schedule)
        self.add_eps(events, show)
        return 



    def veyepar(self, schedule, show):
        # importing from some other instance
        rooms = self.snake_holes(schedule)
        # hack because the veyepar export doesn't give room name
        # will fix when I need to.
        # rooms = ['CrowdSPRING']
        rooms = [ str(r) for r in rooms ]
        self.add_rooms(rooms,show)

        events = self.snake_bites(schedule,rooms[0])
        self.add_eps(events, show)
        return 


    def desktopsummit(self, schedule, show):
        rooms = set(row[2] for row in schedule)
        self.add_rooms(rooms,show)

        events=[]
        for row in schedule:
            if self.options.verbose: print row
            event={}
            event['id'] = row[0]
            event['name'] = row[1]
            event['location'] = row[2]
            dt_format='%a, %Y-%m-%d %H:%M'
            event['start'] = datetime.datetime.strptime(
                    row[3], dt_format)
            end = datetime.datetime.strptime(
                    row[4], dt_format)

            seconds=(end - event['start']).seconds 
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = row[5]
            event['emails'] = ''
            event['released'] = True
            event['license'] = self.options.license
            event['description'] = ''
            event['conf_key'] = row[0]

            event['conf_url'] = row[6]
            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = row

            events.append(event)
 

        self.add_eps(events, show)
        return 


    def ddu(self, schedule, show):
        # drupal down under 2012
        rooms = self.get_rooms(schedule,'room')
        self.add_rooms(rooms,show)

        events = self.ddu_events(schedule)
        self.add_eps(events, show)
        return 



    def zoo(self, schedule, show):
        rooms = self.zoo_cages(schedule)
        self.add_rooms(rooms,show)

        # rooms=['Cafeteria', 'Caro', 'Studio', 'C001', 'T101', 'Studio 1', 'Studio 2', 'Studio 3', 'B901', 'T102', 'Mercure Ballarat', 'Mystery Location', 'Ballarat Mining Exchange']
        # good rooms=['Caro', 'Studio', 'C001', 'T101', ]

        bad_rooms=['Cafeteria', 'Studio 1', 'Studio 2', 'Studio 3', 'B901', 'T102', 'Mercure Ballarat', 'Mystery Location', 'Ballarat Mining Exchange']
        locs=Location.objects.filter(name__in = bad_rooms)
        for loc in locs:
            loc.active = False
            loc.save()

        events = self.zoo_events(schedule)
        self.add_eps(events, show)
        return 


    def fos_events( self, schedule ):
 
        events = []
        id = 0

        # schedule[0] is <conference></conference>
        for day in schedule[1:3]:
            # >>> schedule[1].get('date')
            # '2012-02-04'
            start_date = day.get('date')
            print start_date
            for room in day:
                for row in room:
                    # >>> event.find('start').text
                    # '10:30'
                    # >>> [x.tag for x in event]
                    tags = ['start', 'duration', 'room', 'slug', 'title', 'subtitle', 'track', 'type', 'language', 'abstract', 'description', 'persons', 'links']
                    for tag in tags:
                        print tag, row.find(tag).text

                    event={}
                    # event['id'] = row[0]
                    event['name'] = row.find('title').text

                    event['location'] = row.find('room').text

                    dt_format='%Y-%m-%d %H:%M'
                    event['start'] = datetime.datetime.strptime(
                            "%s %s" % ( start_date,row.find('start').text),
                            dt_format)

                    event['duration'] = \
                        "%s:00" % row.find('duration').text
                    
                    persons = [p.text for p in 
                            row.find('persons').getchildren() ]
                    event['authors'] = ', '.join(persons)

                    event['emails'] = ''
                    event['released'] = True
                    event['license'] = self.options.license
                    # event['description'] = row.find('description').text
                    event['description'] = row.find('abstract').text

                    event['conf_key'] = id

                    event['conf_url'] = ''
                    event['tags'] = ''

                    # save the original row so that we can sanity check end time.
                    event['raw'] = row

                    events.append(event)
                    id += 1
         
        return events


    def fosdem2012(self, schedule, show):

        # top of schedule is:
        # <conference></conference>
        # <day date="2012-02-04" index="1"></day>
        # <day date="2012-02-05" index="2"></day>
        # each day has a list of rooms

        rooms = [ r.get('name') for r in schedule[1] ]
        rooms = set( rooms )
        # probabalby the same rooms the 2nd day.
        rooms = list(rooms)
        # ['Janson', 'K.1.105', 'Ferrer', 'H.1301', 'H.1302']
        self.add_rooms(rooms,show)

        events = self.fos_events(schedule)
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
        # url='http://pyohio.org/schedule/json/'
        # url='https://www.desktopsummit.org/program/veyepar.csv'
        # url='http://pycon-au.org/2011/conference/schedule/events.json'


        # url='http://djangocon.us/schedule/json/'
        # url='http://pygotham.org/talkvote/full_schedule/'
        # url='http://www.pytexas.org/2011/schedule/json/'

        if self.args:
            url = self.args[0]
        else:
            url = { 
            'djangocon2011': 'http://djangocon.us/schedule/json/',
            'pygotham': 'http://pygotham.org/talkvote/full_schedule/',
            'pytexas_2011': 'http://www.pytexas.org/2011/schedule/json/',
            'pyconde2011': 'http://de.pycon.org/2011/site_media/media/wiki/mediafiles/pyconde2011_talks.json',
            'ddu_2012': "http://drupaldownunder.org/program/session-schedule/json",
            'lca_2012': "http://lca2012.linux.org.au/programme/schedule/json",
            'fosdem_2012': "http://tmp.fosdem.org/video.xml",
            'pycon_2012': "https://us.pycon.org/2012/schedule/json/",
            'xpycon_2012': "file://pc2012.json",
            }[self.options.show]

        if self.options.verbose: print url

        if url.startswith('file'):
            f = open(url[7:])
        else:
            req = urllib2.Request(url)
            # req.add_header('Content-Type', 'application/json')
            req.add_header('Accept', 'application/json')
            response = urllib2.urlopen(req)

            # f=urllib2.urlopen(url)
            f = response

        if url[-4:]=='.csv':
            schedule = list(csv.reader(f))
            if 'desktopsummit.org' in url:
                return self.desktopsummit(schedule,show)
        elif url[-4:]=='.xml':
            import xml.etree.ElementTree
            x = f.read()
            schedule=xml.etree.ElementTree.XML(x)
            return self.fosdem2012(schedule,show)
        else:
            j=f.read()
            schedule = json.loads(j)


        # save for later
        file('schedule.json','w').write(j) 
        # j=file('schedule.json').read()

        # look at fingerprint of file, call appropiate parser

        if self.options.show == 'pyconde2011':
            # pycon.de 2011 
            return self.pyohio(schedule,show)
            # return self.pyconde2011(schedule,show)

        if j.startswith('{"files": {'):
            # doug pycon, used by py.au
            return self.pctech(schedule,show)

        if j.startswith('[{"pk": '):
            # veyepar show export
            return self.veyepar(schedule,show)

        if j.startswith('[{"') and schedule[0].has_key('room_name'):
            # PyCon 2012
            return self.symposium(schedule,show)

        if j.startswith('[{"') and schedule[0].has_key('last_updated'):
            # pyohio
            return self.pyohio(schedule,show)

        if j.startswith('[{"') and schedule[0].has_key('start_iso'):
            # pyTexas
            return self.pyohio(schedule,show)

        if j.startswith('[{"') and schedule[0].has_key('talk_day_time'):
            # pyGotham
            return self.pygotham(schedule,show)

        if url.endswith('programme/schedule/json'):
            # Zookeepr
            return self.zoo(schedule,show)

        if url.endswith('program/session-schedule/json'):
            # ddu 2012
            schedule = [s['session'] for s in schedule['ddu2012']]
            # pprint.pprint( schedule )
            s_keys = schedule[0].keys()
            print s_keys
            v_keys=('id',
                'location','sequence',
                'name','slug', 'authors','emails', 'description',
                'start','duration', 
                'released', 'license', 'tags',
                'conf_key', 'conf_url',
                'host_url', 'publiv_url',
        )    
            print [k for k in v_keys if k in s_keys]
            print [k for k in v_keys if k not in s_keys]

            return self.ddu(schedule,show)

        # schedule = schedule['nodes']
        # self.addlocs(schedule,show)
        # self.addeps(schedule, show)
        return

    def add_more_options(self, parser):
        parser.add_option('-f', '--filename', default="talks.csv",
          help='csv file' )
        parser.add_option('-u', '--update', action="store_true", 
          help='update when diff, else print' )
        parser.add_option('-L', '--license', 
          help= "http://creativecommons.org/licenses/" )

    def add_more_option_defaults(self, parser):
        parser.set_defaults(license='CC BY-SA')


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

            rfs = Raw_File.objects.filter(show=show)
            if rfs and not self.options.force:
                print "There are Raw Fiels... --force to whack."
                print rfs
                print "whacking aborted."
                return False

            rfs.delete()
            Episode.objects.filter(show=show).delete()

        self.one_show(show)

if __name__ == '__main__':
    p=add_eps()
    p.main()

