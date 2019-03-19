#!/usr/bin/env python

# adds episodes from an external source, like a json file or url.

"""
fields:
title - Talk title
speakers - list of:
  name - person's name.
  email - email address (hide behind auth)
  twitter_id - twitter @username
  bio - info about the person
  picture_url - head shot
summary - short description of talk, 1 or 2 lines.
description - description of the talk (paragraphs are fine, markdown great)
tags - list of serch terms, including sub topics briefly discussed in the talk.
room - room as described/labled by the venue
room_alias - room as described/labled on conference site
start - '%Y-%m-%dT%H:%M:%S' "2014-11-15T16:35:00",
end - (provide end or duration)
duration - int minutes (preferred)
priority - 0=no video, 5 = maybe video, 9=make sure this gets videod.
released - speakers have given permission to record and distribute.
license - CC license
reviewers - email addresses of person(s) who will double check this video
conf_key - PK in source database - unique, used to update this item
conf_url - URL of talk page
language - Spoken language of the talk ("English")
"""

"""
NOTE: In general it is better to build the export as simple as posible,
even at the expense of deviating from the above fields.  Exporting extra
fields is just fine.  They will be ignored, or maybe I will use them in
a future version.

For fields yuou don't have, plug in a value.  If you don't have 'released'
give me "Yes" and then let the presenters know.

End and Duration:  give me what you have in your database

I can fix my consumer easier than I can get someone else's website updated.

See also:
    https://github.com/pinax/symposion
    https://github.com/chrisjrn/symposion

    https://github.com/pyohio/pyohio-website
    https://strptime.com/

columns
['conf_key', 'start', 'duration', 'title', 'authors', 'twitter_id', 'emails', 'reviewer', 'released', 'conf_url', 'license']

"""

def mk_fieldlist():
    fields = []
    for line in __doc__.split('\n'):
        if '-' in line:
            field,desc = line.split(' - ',1)
            fields.append(field)

    print("""printf '{}\\n'|xclip -selection clipboard""".format('\\t'.join(fields)))

# FireFox plugin to view .json data:
# https://addons.mozilla.org/en-US/firefox/addon/10869/

from datetime import datetime, timedelta
import csv
import html.parser
import os
import pytz
import re
import requests

import urllib.parse

from pprint import pprint
from difflib import Differ
from requests.packages.urllib3.exceptions import InsecureRequestWarning

from dateutil.parser import parse
# import dateutil
from django.utils.html import strip_tags
from django.template.defaultfilters import slugify

import operator

import xml.etree.ElementTree

from bs4 import BeautifulSoup

import json

# import gdata.calendar.client
# import gdata.calendar.service

from icalendar import Calendar, Event
from icalendar import vDatetime

from django.utils.timezone import localtime

# for goog spreassheet api
# https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/
from apiclient.discovery import build
from httplib2 import Http
# from oauth2client import file, client, tools
import oauth2client # import file, client, tools

# for google calandar:
# import lxml.etree
from lxml import html

import pw

import process

from main.models import Client, Show, Location, Episode, Raw_File


def fix_twitter_id(twitter_ids):

    if twitter_ids is None:
        return ''

    ret = []
    for tid in re.split('[ ,]',twitter_ids):
        tid = tid.strip()
        if tid.startswith('#'):
            # leave this alone
            pass
        elif tid and not tid.startswith('@'):
            # print('2 {}.'.format(tid))
            tid = "@" + tid
        ret.append(tid)

    ret = ', '.join(ret)
    return ret

def goog(show,url):

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
        print("fcal title:", fcal.title.text)
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

            print(goo_start)
            start = datetime.strptime(goo_start,'%Y-%m-%dT%H:%M:%S.000-05:00')
            end = datetime.strptime(goo_end,'%Y-%m-%dT%H:%M:%S.000-05:00')


            minutes = delta.seconds/60 # - 5 for talk slot that includes break
            hours = minutes/60
            minutes -= hours*60

            duration="%s:%s:00" % ( hours,minutes)

            # print name, authors, location, start, duration
            print("%s: %s - %s" % ( authors, location, start.time() ))

            seq+=1
            # broke this, use add_eps()
            episode,created = xEpisode.objects.get_or_create(
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

def googsheet(spreadsheetId, range_name='A1:ZZ99999'):
    # read from goog spreadsheet

    """
    range is any
https://developers.google.com/resources/api-libraries/documentation/sheets/v4/python/latest/sheets_v4.spreadsheets.values.html#get

    you can define a named range in the spreadsheet name, like "veyepar"
    (this is a good idea.)

    whatever the range is:
    top row of that range will be dictionary keys
    remaining rows will be data.
    """

    # Setup the Sheets API
    SCOPES = 'https://www.googleapis.com/auth/spreadsheets.readonly'
    store = oauth2client.file.Storage('credentials.json')
    creds = store.get()
    if not creds or creds.invalid:
        flow = oauth2client.client.flow_from_clientsecrets(
                'client_secret.json', SCOPES)
        creds = oauth2client.tools.run_flow(flow, store)
    service = build('sheets', 'v4', http=creds.authorize(Http()))

    # import code; code.interact(local=locals())

    result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheetId,
            range=range_name).execute()

    values = result.get('values', [])
    if not values:
        print('No data found.')
        import code; code.interact(local=locals())

    else:
        keys=values[0]
        print("keys: {}".format(keys))
        rows=[]
        for row in values[1:]:
            row.append(None)
            rowd = dict(zip(keys, row))
            rows.append(rowd)

    return rows


class add_eps(process.process):

    # helpers

    def dump_keys(self, schedule):

        # try to print out what keys match and don't match
        # prints out the veyepar side of the field map list
        # so you can cut/paste it into the show specific code.

        # if the json object is one big key:value, pull the list out
        try:
            keys= list(schedule.keys())
            key = keys[0]
            # schedule=schedule['schedule']
            schedule=schedule[key]
        except AttributeError as k:
            # AttributeError: 'list' object has no attribute 'keys'
            pass
        except TypeError as k:
            # TypeError: list indices must be integers, not str
            pass
        except KeyError as k:
            print(k)
            if k != 'schedule': raise

        s_keys = set()
        for s in schedule:
            print(s)
            s_keys.update(list(s.keys()))

        print("keys found in input:")
        print(s_keys)
        for k in s_keys:
            print(("('{}',''),".format(k)))
        print("\n")

        v_keys=('id',
            'location','sequence',
            'name','slug',
            'authors', 'emails', 'twitter_id', 'reviewers',
            'start','duration',
            'released', 'license', 'tags',
            'conf_key', 'conf_url',
            'host_url', 'public_url',
    )

        # for f,g in field_maps:
        #    print "('%s','%s')," % (g,f)

        print("keys match 1:1 with veyepar names:")
        print([k for k in v_keys if k in s_keys])

        for k in [k for k in v_keys if k not in s_keys]:
            print(("('{}',''),".format(k)))
        print("\n")

        for k in v_keys:
            k2 = k if k in s_keys else ''
            print("('%s','%s')," % (k2,k))
        print()

        # lines to mix n match in the editor
        for k in s_keys:
            print("('%s'," % (k,))
        print()
        for k in v_keys:
            print("'%s')," % k)
        print()


        return

    def add_rooms(self, rooms, show):

      if self.options.test:
            print("test mode, not adding locations to db\n")
            return

      if not self.options.update:
            print("no --update, not adding locations to db\n")
            return

      rooms = sorted(rooms)

      seq=0
      for room in rooms:
          if self.options.verbose: print(room)
          seq+=10

          # __iexact won't work with ger_or_add to don't try to use it
          try:
              loc = Location.objects.get(name__iexact=room)
          except Location.DoesNotExist:
              slug = slugify(room).replace('-','_')
              loc = Location(name=room, sequence=seq, slug=slug)
              loc.save()

          show.locations.add(loc)
          show.save()


    def generic_events(self, schedule, field_maps ):

        # step one in transforming the show's data into veyepar data

        # field_maps is a list of (source,dest) field names
        # if source is empty, the create the dest as ''
        # if there is an error (like key does not exist in source),
        #   create dest as None

        # TODO:
        # consider only creating destination when there is proper source.
        # current code make add_eps() simpler.
        # something has to contend with whacky source,
        #  currently it is this.

        events=[]
        for row in schedule:
            if self.options.verbose: print(row)
            event={}

            for jk,vk in field_maps:  # json key, veyepar key
                if jk:
                    # if self.options.verbose: print jk, row[jk]
                    try:
                        if '{' in jk:
                            #  ('{date}T{start}', 'start'),
                            event[vk] = jk.format(**row)
                        else:
                            event[vk] = row[jk]
                    except:
                        event[vk] = None
                        # pass
                else:
                    event[vk] = ''

            # save the original row so that we can sanity check end time.
            # or transform data
            event['raw'] = row

            events.append(event)

        return events

    def add_eps(self, schedule, show):
        """
        Given a list of dicts,
           diff aginst current veyepar db
           or update the db.
        """

        # options:
        # test - do nothing.  Test is for testing the transfromations.
        # update - update the db.
        #   no update will show diff between real and db

        # Notes:
        # location - room name as stored in Location model.
        #   considering changing it to the ID of the location record.
        #
        # raw - the row from the input file before any transormations.

        # TODO:
        # add a "lock" to prevent updates to a record.
        # need to figure out what to do with colisions.

        # only these fields in the dict are used, the rest are ignored.
        fields=(
                # 'state',
                'name', 'authors',
                'emails',
                'twitter_id',
                'reviewers',
                'description',
                'start','duration',
                'released',
                'license',
                'conf_url', 'tags',
                # 'host_url',  # for pycon.ca youtube URLs
                )

        if self.options.test:
            print("test mode, not adding to db")
            return

        seq=0
        for row in schedule:
            if self.options.verbose: pprint( row )

            # try to find an existing item in the db

            episodes = Episode.objects.filter(
                      show=show,
                      conf_key=row['conf_key'],
                      )

            if episodes:
                if len(episodes)>1:
                    # There should not be more than 1.
                    # this means the uniquie ID is not unique,
                    # and there is a dube in the veyepar db.
                    # import pdb; pdb.set_trace()
                    print("fuond dupe!")
                    import code; code.interact(local=locals())
                    # then continue on.

                episode = episodes[0]
                # have an existing episode,
                # either update it or diff it.

                # get rid of garbage that snuck into the db.
                if episode.emails == "<redacted>":
                    episode.emails = ""

                # special case for email: don't blank it out
                # use what is in the db.
                # up here and now below so the diff doesn't wazz
                # if episode.emails and not row['emails']:
                #    row['emails'] = episode.emails
            else:
                episode = None

            # this is the show diff part.
            diff=False
            if episode is None:
                diff=True
                print("{conf_key} not in db, name:{name}\n{location}".format(
                        **row))
                print()

            else:
                # print("tags", episode.tags.__repr__(), row['tags'].__repr__())
                # check for diffs
                diff_fields=[]

                if episode.location is None or \
                        episode.location.name.upper() != row['location'].upper():
                    diff=True
                    if episode.location is None:
                        diff_fields.append(('loc',
                            "(None)", row['location']))
                    else:
                        diff_fields.append(('loc',
                            episode.location.name, row['location']))
                    # print(episode.location.name, row['location'])

                for f in fields:
                    # veyepar, remote
                    a1,a2 = getattr(episode,f), row[f]

                    if f=="emails":
                        # don't always have rights to get email
                        if not a2:
                            continue

                    if f=="description":
                        a1 = a1.replace('\r','')
                        a2 = a2.replace('\r','')

                    if (a1 or a2) and (a1 != a2):
                        diff=True
                        diff_fields.append((f,a1,a2))

                # report if different
                if diff:
                    print('veyepar #id name: #%s %s' % (
                            episode.id, episode.name))
                    host= "veyepar.nextdayvideo.com"
                    print("http://%s/main/E/%s/" % ( host, episode.id, ))
                    print(episode.conf_key, episode.conf_url)
                    if self.options.verbose:
                        pprint( diff_fields )
                    for f,a1,a2 in diff_fields:
                        if self.options.verbose:
                            print(1, a1.__repr__())
                            print(2, a2.__repr__())
                        if not isinstance(a1,str):
                            print('veyepar {0}: {1}'.format(f,a1))
                            print('   conf {0}: {1}'.format(f,a2))
                        else:
                            print(f)
                            d = Differ()
                            text1 = a1.split('\n')
                            text2 = a2.split('\n')
                            result = list(d.compare(text1, text2))
                            # pprint(result)

                            if a2 is None or max(len(a1),len(a2)) < 160:
                              # print a1
                              # print a2
                              print('veyepar {0}: {1}'.format(f,a1))
                              print('   conf {0}: {1}'.format(f,a2))
                            else:
                              # long string (prolly description)
                              for i,cs in enumerate(zip(a1,a2)):
                                if cs[0] != cs[1]:
                                    """
                                    print \
                      "#1, diff found at pos {0}:\n{1}\n{2}".format(
                              i,cs[0].__repr__(),
                                cs[1].__repr__())
                                    """
                                    print(
                                        "diff found at pos {0}".format(i))
                                    """
                                    print(
                                        "veyepar: {1}\n   conf: {2}".format(                               a1[i:i+80].__repr__(),
                                a2[i:i+80].__repr__()))
                                    """
                                    break
                    print()


            """
            if diff and episode.state > 5: # add_to_richard
                print(u"not updating conf_key: {conf_key}, name:{name}".format(**row))
                print(episode.public_url)
                print()
                continue
            """

            if self.options.update and diff:
                if episode is None:
                    print("adding conf_key: %(conf_key)s, name: %(name)s" % row)
                    # I am not sure why some fields are here in .create
                    # and the rest are in setattr( episode, f, row[f] )
                    # name is here so .save() will create a slug

                    episode = Episode.objects.create(
                          show=show, conf_key=row['conf_key'],
                          start=row['start'],
                          duration=row['duration'],
                          name=row['name'],
                          )
                    episode.sequence=seq
                    episode.state=1
                    seq+=1

                else:
                    print(("updating conf_key: {conf_key}, name:{name}").format(**row))

                location=Location.objects.get(
                        name__iexact=row['location'])

                episode.location = location

                if self.options.reslug:
                    episode.slug=''

                # copy all the fields
                # from the source row to the episode object
                for f in fields:
                    setattr( episode, f, row[f] )

                # save whatever data was passed
                # episode.conf_meta=json.dumps(row['raw'])

                episode.save()

        print("checking for removed talks...")
        conf_keys = [str(row['conf_key']) for row in schedule]
        episodes = Episode.objects.filter( show=show, )
        for ep in episodes:
            if ep.conf_key not in conf_keys:
                print("#{id} name:{name}\n"
                  "ep.conf_key:{conf_key} conf_url: {conf_url}\n".format(
                           id=ep.id,
                           state=ep.state,
                           conf_key=ep.conf_key,
                           conf_url=ep.conf_url,
                           name=ep.name))


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
          if self.options.verbose: print(row)
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
            print(row)

    def  talk_time(self, day, time):
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

          # start=datetime.strptime(row['Start'], '%Y-%m-%d %H:%M:%S' )
          # start=datetime.strptime(row['Start'],'%m/%d/%y %I:%M %p')

          # pycon dates:
          # [ 2010, 9, 7, 15, 0 ]
          # start = datetime(*row['start'])

          # minutes = row['duration']

          # adjust for time zone:
	  # start += datetime.timedelta(hours=-7,minutes=0)


    def str2bool(self, tf):
        return {'true':True,
                "false":False}[tf]

    def snake_bites(self, schedule,):
        print("Snake Bites")

        fields=(
                'location',
                'sequence',
                'conf_key','host_url',
            'state',
            'authors',
            'name','slug',
            'authors',
            'emails',
            'description',
            'released', 'license',
            'start','duration',
            'conf_key',
            'conf_url', 'tags',
            # 'public_url'
            )

        events=[]
        for row in schedule:
            pk = row['pk']

            row = row['fields']
            if self.options.verbose: print(row)
            event={}
            for f in fields:
                event[f] = row[f]

            # fields that don't flow thought json that nice.
            if not event['conf_key']: event['conf_key'] = "pk{}".format(pk)
            event['start'] = datetime.strptime(
                    row['start'], '%Y-%m-%dT%H:%M:%S' )

            events.append(event)

        return events

    def zoo_events(self, schedule):
        events=[]
        for row in schedule:
            if self.options.verbose: print(row)
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

            # from /zookeepr/controllers/schedule.py
            # row['Id'] = schedule.id
            # row['Event'] = schedule.event_id
            # I think Id is what is useful
            event['conf_key'] = row['Id']

            event['name'] = row['Title']
            event['location'] = row['Room Name']
            event['start'] = datetime.strptime(
                    row['Start'], '%Y-%m-%d %H:%M:%S' )
            event['duration'] = row['Duration']
            event['authors'] = row.get('Presenters','')

            if not event['authors'] and " : " in row['Title']:
                if event['conf_key'] not in [207,364,]:
                    event['name'],event['authors'] = row['Title'].split(" : ")

            # https://github.com/zookeepr/zookeepr/issues/92
            event['emails'] = row.get('Presenter_emails','')

            # https://github.com/zookeepr/zookeepr/issues/93
            # new code.. seems I either get True or no attribute.
            event['released'] = {
                    'True':True, 'False':False, None:None}[
                            row.get('video_release',None)]
            # easy way:
            # make True the default
            event['released'] = row.get('video_release',"True") == "True"

            event['license'] = "CC-BY-SA"

            event['description'] = row['Description']

            # there may not be a URL, like for Lunch and Keynote.
            # https://github.com/zookeepr/zookeepr/issues/91
            event['conf_url'] = row.get('URL','')

            event['tags'] = ''
            event['twitter_id'] = ''

            event['raw'] = row

            events.append(event)

        return events

    def zoo_cages(self, schedule):
      rooms=[]
      for row in schedule:
          # row=row['node']
          if self.options.verbose: print(row)
          room = row['Room Name']
          if room not in rooms: rooms.append(room)

      if self.options.verbose: pprint(rooms)

      return rooms


    def get_rooms(self, schedule, key='location'):
      rooms=set()
      for row in schedule:
          if self.options.verbose: print(row)
          room = row[key]
          if room is None: room = "None"
          rooms.add(room)
      return rooms


    def symp_events(self, schedule ):
        events=[]

        for row in schedule:
            if self.options.verbose: pprint( row )
            event={}
            # event['id'] = row['conf_url']
            # event['id'] = row['id']
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

            event['start'] = datetime.strptime(
                    row['start_iso'], '%Y-%m-%dT%H:%M:%S' )

            # if "Poster" in row["tags"]:
            # event['start'] += datetime.timedelta(hours=-3)

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
            event['conf_key'] = row['url']
            event['conf_url'] = row['url']

            if event['conf_key'] is None: event['conf_key'] = ""
            if event['conf_url'] is None: event['conf_url'] = ""

            event['conf_key'] = event['conf_key'][-5:]

            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = row

            events.append(event)

        return events

    def ddu_events(self, schedule ):
        # Drupal Down Under 2012

        html_parser = html.parser.HTMLParser()

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
            if self.options.verbose: print(row)
            event={}

            for k in common_fields:
                try:
                    event[k] = row[k]
                except KeyError:
                    event[k] = 'missing'

            for k1,k2 in field_map:
                event[k1] = row[k2]

            if isinstance(event['authors'],dict):
                event['authors'] = ", ".join( list(event['authors'].values()) )

            if row["entities"] == "true":
                for k in html_encoded_fields:
                    # x = html_parser.unescape('&pound;682m')
                    event[k] = html_parser.unescape( event[k] )


            # x = html_parser.unescape('&pound;682m')

            event['start'] = datetime.strptime(
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

    def flourish_events(self, schedule ):
        # flourish 2012

        # these fields exist in both json and veyepar:
        common_fields = [ 'name', 'description',
            'authors', 'contact',
            'start', 'end',
            'released', 'license', 'tags', 'conf_key', 'conf_url']

        # mapping of json to veyepar:
        field_map = [
                ('emails','contact'),
                ('location','room'),
                ]

        events=[]
        for row in schedule:
            if self.options.verbose: print(row)
            event={}

            for k in common_fields:
                try:
                    event[k] = row[k]
                except KeyError:
                    event[k] = 'missing'

            for k1,k2 in field_map:
                event[k1] = row[k2]

            event['start'] = datetime.strptime(
                    event['start'], '%m/%d/%Y %H:%M:%S' )

            event['end'] = datetime.strptime(
                    event['end'], '%m/%d/%Y %H:%M:%S' )

            delta = event['end'] - event['start']
            seconds=delta.seconds

            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            # save the original row so that we can sanity check end time.
            event['raw'] = row

            events.append(event)

        return events


    def chipy_events(self, schedule ):

        # mapping of json to veyepar:
        field_maps = [
                ('id', 'conf_key'),
                ('title', 'name'),
                ('description', 'description'),
                ('presentors', 'authors'),
                ('presentors', 'emails'),
                ('start_time', 'start'),
                ('length', 'duration'),
                ('', 'conf_url'),
                ('', 'tags'),
                ]

        events = self.generic_events(schedule, field_maps)
        for event in events:
            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%d %H:%M:%S' )

            event['authors'] =  event['authors'][0]['name']
            event['emails'] =  event['emails'][0]['email']
            event['location'] = 'room_1'
            event['released'] = True
            event['license'] = ''
            event['duration'] = event['duration'] + ":00"

        return events

    def goth_events(self, schedule ):
        # PyGotham 2011

        field_maps = [
                ('room_number','location'),
                ('title','name'),
                ('full_name','authors'),
                ('talktype',''),
                ('levels',''),
                ('key','conf_key'),
                ('talk_day_time','start'),
                ('duration_minutes','duration'),
                ('talk_end_time','end'),
                ('outline',''),
                ('desc','description'),
                ('','conf_url'),
                ('','released'),
                ('','emails'),
                ('','license'),
                ('','tags'),
               ]

        events = self.generic_events(schedule, field_maps)
        for event in events:

            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%d %H:%M:%S' )

            seconds=(event['duration'] -10) * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

        return events

    def pct_events(self, schedule):
        # pyCon Tech
        # >>> schedule['events']['28'].keys()
        # [u'files', u'room', u'videos', u'title', u'url', u'id', u'tags', u'shorturl', u' sponsors', u'summary', u'presenters', u'duration', u'level', u'type', u'start']

        events=[]
        for event_id in schedule['events']:
          src_event=schedule['events'][event_id]
          if self.options.verbose: print(src_event)
          if src_event['type'] != 'Social Event':
            event={}
            # event['id'] = event_id
            event['name'] = src_event['title']
            event['location'] = schedule['rooms'][src_event['room']]['name']

            event['start'] = datetime(*src_event['start'])

            seconds=src_event['duration'] * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = src_event['presenters']
            event['emails'] = ''
            event['license'] = self.options.license
            event['description'] = src_event['summary']
            event['conf_key'] = src_event['id']

            event['conf_url'] = src_event['url']
            event['tags'] = ''

            # save the original row so that we can sanity check end time.
            event['raw'] = src_event

            events.append(event)

        return events

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

    def symposion_chrisjrn(self, schedule, show):
        schedule = schedule['schedule']

        plenary_room = "Mystic Theatre"

        video_types = (
'plenary',
'Keynote',
'Lightning Talks and Conference Closing',
'Lightning Talks',
'Conference Closing',
'talk',
'tutorial',
'miniconf',
'Conference Opening',
'Linux Australia Annual General Meeting',
'Free Software Law & Policy Miniconf Session',
'Docs Down Under Miniconf Session',
'Opening Remarks and Housekeeping',
'WOOTCONF Session',
'Games and FOSS Session',
'Open Knowledge Session',
'Kernel Session',
'housekeeping',
                )

        not_video_kinds = (
'break',
'other',
'nothing',
                )

        # Remove types of itmes that aren't for video
        # schedule = [s for s in schedule if s['kind'] in video_types ]

        # remove empty slots
        # bad_keys = (80, 82, 91, 100, 102, 103)
        # schedule = [s for s in schedule if s['conf_key'] not in bad_keys ]
        # remove enteries that don't have authors
        # schedule = [s for s in schedule if "authors" in s]

        # Remove kinds of itmes that aren't for video
        schedule = [s for s in schedule
                if s['kind'] not in not_video_kinds ]

        schedule = [s for s in schedule if s['name'] != 'Slot' ]
        for s in schedule:
            if s['name'] == 'Slot':
                pprint( s )


        field_maps = [
                ('room','location'),
                ('name','name'),
                ('abstract','description'),
                ('authors','authors'),
                ('contact','emails'),
                ('twitter_id','twitter_id'),
                ('reviewers','reviewers'),
                ('start','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                # ('tags','tags'),
                ('track','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
                ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            if self.options.verbose: pprint(event['raw'])

            if event['raw']["kind"] in ["talk", "Not Talk"] and not event['location']:
                event['location'] = plenary_room

            if plenary_room in event['location']:
                event['location'] = plenary_room

            event['name'] =  re.sub( r'[\n\r]', ':)', event['name'] )

            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%dT%H:%M:%S' )

            event['duration'] =   "0:{}:0".format(event['duration'])

            event['emails'] =  ', '.join(
                    a['contact'] for a in event['authors'] )
            event['twitter_id'] =   fix_twitter_id(','.join(
                    a['twitter'] for a in event['authors'] ) )
            event['picture_url'] =  ', '.join(
                    a['picture_url'] for a in event['authors'] )
            event['authors'] =  ', '.join(
                    a['name'] for a in event['authors'] )


            """
            if event['authors'] is None:
                event['authors'] =  ''
            else:
                event['authors'] =  ', '.join( event['authors'] )

            if event['emails'] == ["redacted",]:
                print('emails redacted!')
                return
                event['emails'] =  ""
            else:
                event['emails'] =  ', '.join( event['emails'] )
            event['twitter_id'] = fix_twitter_id(event['twitter_id'])
            """

            if event['conf_url'] is None:
                event['conf_url'] =  ''

            if event['description'] is None:
                event['description'] =  ''

            if event['reviewers'] is None:
                event['reviewers'] =  ''



        rooms = self.get_rooms(events,'location')
        self.add_rooms(rooms,show)
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
        rooms = self.get_rooms(schedule,'room')
        rooms = [r for r in rooms if r != 'Plenary' ]
        self.add_rooms(rooms,show)

        events = self.symp_events(schedule)
        for e in events:
            print(e)
            end  = datetime.strptime(
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
        rooms = list(rooms)
        rooms.sort()
        print(rooms)
        self.add_rooms(rooms,show)

        events = self.goth_events(schedule)
        self.add_eps(events, show)
        return

    def scipy_events_v1(self, schedule ):
        # SciPy 2012, ver 1

        # mapping of json to veyepar:
        field_maps = [
            ('Room','location'),
            ('Name','name'),
            ('speaker',''),
            ('Authors','authors'),
            ('Contact','emails'),
            ('Tags','tags'),
            ('abstract','description'),
            ('Start','start'),
            ('Duration','duration'),
            ('End','end'),
            ('Affiliations',''),
            ('','conf_key'),
            ('','conf_url'),
            ('','released'),
            ('','license'),

            ]

        events = self.generic_events(schedule, field_maps)
        for event in events:
            # print event['raw']
            # print (event['location'], event['start'])
            event['conf_key'] = hash(str(event['location']) + event['start'])

            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%dT%H:%M:%S' )

            # seconds=int(event['duration']) * 60
            # hms = seconds//3600, (seconds%3600)//60, seconds%60
            # duration = "%02d:%02d:%02d" % hms
            # event['duration'] =  duration

        return events

    def scipy_events(self, schedule ):
        # SciPy 2012, ver 3

        common_fields = [ 'name', 'description',
            'authors',
            'start', 'duration', 'end',
            'released', 'license', 'tags', 'conf_key', ]

        # mapping of json to veyepar:
        field_maps = [
            ('contact','emails'),
            ('','conf_url'),
            ('room','location'),
            ]

        events = self.generic_events(schedule, field_maps)
        for event in events:
            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%d %H:%M:%S' )
            event['duration'] = event['duration'] + ":00"

            # released flag fliping back to False?
            # investigate later, ignore for now.
            # event['released'] = event['released']!="0"
            # del(event['released'])

            if event['description'] is None:
                event['description'] = "None"

        return events


    def scipy_v1(self, schedule, show):
        # scipy ver 1 2011

        # schedule is {'talks':[talk1, 2, 3...]}
        schedule = schedule['talks']
        rooms = self.get_rooms_v1(schedule,'Room')
        rooms = list(rooms)
        rooms.sort()
        self.add_rooms(rooms,show)

        events = self.scipy_events(schedule)
        self.add_eps(events, show)
        return



    def scipy_v2(self, schedule, show):
        # scipy ver 2 2011

        for row in schedule:
            if row['room'] is None:
                row['room'] = "None"

        rooms = self.get_rooms(schedule)
        rooms = list(rooms)
        rooms.sort()
        self.add_rooms(rooms,show)

        events = self.scipy_events(schedule)
        self.add_eps(events, show)
        return

    def veyepar(self, schedule, show):
        events = self.snake_bites(schedule)

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)
        return


    def desktopsummit(self, schedule, show):
        rooms = set(row[2] for row in schedule)
        self.add_rooms(rooms,show)

        events=[]
        for row in schedule:
            if self.options.verbose: print(row)
            event={}
            event['id'] = row[0]
            event['name'] = row[1]
            event['location'] = row[2]
            dt_format='%a, %Y-%m-%d %H:%M'
            event['start'] = datetime.strptime(
                    row[3], dt_format)
            end = datetime.strptime(
                    row[4], dt_format)

            seconds=(end - event['start']).seconds
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            event['authors'] = row[5]
            event['emails'] = ''
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

    def ictev_2013(self, schedule, show):
        field_maps = [
            ('Room', 'location'),
            ('Title', 'name'),
            ('Timestamp', 'start'),
            ('Nid', 'conf_key'),
            ('Presenter', 'authors'),
            ('Keywords', 'tags'),
            ('Link', 'conf_url'),
            ('Duration', 'duration'),
            ('Description', 'description'),
           ]

            # ('Day',
            # ('Time', 'start'),
# 'emails'),
# 'released'),
# 'license'),
# 'host_url'),

        events = self.generic_events(schedule, field_maps)

        rooms = set(row['location'] for row in events)
        self.add_rooms(rooms,show)

        html_parser = html.parser.HTMLParser()

        for event in events:

            event['conf_key'] = event['conf_key'].split('</a>')[0].split('>')[1]

            event['name'] = html_parser.unescape(strip_tags( event['name'] ))

            event['start'] = datetime.fromtimestamp(
                int(event['start'])) + datetime.timedelta(hours=14)

            event['duration'] = "00:%s:00" % ( event['duration'], )

            event['conf_url'] = strip_tags(event['conf_url'])

            # Bogus, but needed to pass
            event['license'] =  ''
            event['emails'] =  ''
            event['released'] =  True

            event['tags'] = "" # strip_tags( event['tags'])
            # pprint(event)

        self.add_eps(events, show)

        return


    def ictev(self, schedule, show):
        print("ictev")

        # drupal down under 2012
        rooms = self.get_rooms(schedule, "Room", )
        self.add_rooms(rooms,show)
        # print rooms

        # these fields exist in both json and veyepar:
        common_fields = [ ]

        # mapping of json to veyepar:
        # thise are veyepar to json - need to be flipped to make work
        backward_field_maps = [
                ('location','Room'),
                ('name','Title'),
                ('tags','Keywords'),
                ('duration','Duration'),
                ('conf_key','Nid'),
                ('conf_url','Link')
                ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            row = event['raw']

            if self.options.verbose: print("event", event)

            # authors is either a string or a dict
            # if isinstance(event['authors'],dict):
            #    event['authors'] = ", ".join( event['authors'].values() )

            #
            start, duration = self.talk_time(row['Day'],row['Time'])
            event['start'] = start
            event['duration'] = duration

            event['license'] =  ''
            event['authors'] =  ''
            event['tags'] =  ''
            event['description'] =  ''

            event['emails']=None


        self.add_eps(events, show)
        return

    def unfold_origami_unicorn(self, schedule):
        # dig out the data from
        # {'phpcode_2':{label: "Duration", content: "45"}
        # [{v['label']:v['content'] for v in s.items()} for s in schedule]
        # [{v['label']:v['content'] for v in s.values()} for s in schedule]

        ret_rows = []
        for s in schedule:
            row = {}
            for k in s:
                v = s[k]
                field_name = v['label']
                value = v['content']
                print("#1", field_name, value)
                row[field_name] = value
            pprint(row)
            ret_rows.append(row)

        return ret_rows


    def ddu(self, schedule, show):
        # drupal down under 2012
        rooms = self.get_rooms(schedule)
        self.add_rooms(rooms,show)

        events = self.ddu_events(schedule)
        self.add_eps(events, show)
        return


    def flourish(self, schedule, show):
        rooms = self.get_rooms(schedule)
        self.add_rooms(rooms,show)

        events = self.flourish_events(schedule)
        self.add_eps(events, show)
        return


    def chipy(self, schedule, show):

        # schedule is al meetings ever
        schedule = schedule[-1]['topic_set']
        # pprint( schedule[0] )

        rooms = ['room_1']
        self.add_rooms(rooms,show)

        events = self.chipy_events(schedule)
        self.add_eps(events, show)
        return


    def chipy_v3(self, schedule, show):

        schedule = max(schedule, key=operator.itemgetter('when'))
        when = schedule['when']
        where = schedule['where']
        # ['name']
        pprint( schedule['where'] )

        schedule = schedule['topics']
        schedule = [s for s in schedule if s['approved']]
        # schedule = [s for s in schedule if s['start_time']]
        for s in schedule:
            print((s['title'], s['start_time']))

        field_maps = [
                ('id', 'conf_key'),
                ('title', 'name'),
                ('description', 'description'),
                ('presenters', 'authors'),
                ('presenters', 'emails'),
                ('presenters', 'released'),
                ('license','license'),
                ('start_time', 'start'),
                ('length', 'duration'),
                ('', 'conf_url'),
                ('', 'tags'),
                ('', 'twitter_id'),
                ]

        events = self.generic_events(schedule, field_maps)
        for event in events:
            print("1, event:")
            pprint(event)

            event['location'] = where['name']

            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%dT%H:%M:%S' )

            event['authors'] =  ', '.join(
                    [ a['name'] for a in  event['authors'] ])

            event['emails'] =  ', '.join(
                    [ a['email'] for a in  event['emails']
                        if a['email'] ])

            # if not event['emails']: # no email found
            #    event['emails'] = "ChiPy <chicago@python.org>"

            event['released'] = all(
                    [ a['release'] for a in event['released'] ])

            event['conf_url'] = "http://www.chipy.org/"

        rooms = set(row['location'] for row in events)
        self.add_rooms(rooms,show)

        # __iexact won't work with ger_or_add to don't try to use it
        try:
            loc = Location.objects.get(name__iexact=where['name'])
            loc.description = where['address']
            loc.save()
        except Location.DoesNotExist:
            # test mode I guess
            pass


        self.add_eps(events, show)

        return


    def zoo(self, schedule, show):

        # rooms=['Cafeteria', 'Caro', 'Studio', 'C001', 'T101', 'Studio 1', 'Studio 2', 'Studio 3', 'B901', 'T102', 'Mercure Ballarat', 'Mystery Location', 'Ballarat Mining Exchange']
        # good rooms=['Caro', 'Studio', 'C001', 'T101', ]

        # bad_rooms=['Cafeteria', 'Studio 1', 'Studio 2', 'Studio 3', 'B901', 'T102', 'Mercure Ballarat', 'Mystery Location', 'Ballarat Mining Exchange']

        # bad_rooms = [ 'Costa Hall Foyer', 'uncatered', 'Super Awesome Venue TBA', 'The Pier - http://www.thepiergeelong.com.au', 'Edge Bar, Western Beach Road', ]

        bad_rooms = [
                ' ',
                'Bayview Eden, 6 Queens Road, Melbourne'
                ]


        for s in schedule:

            # Plenarys
            if s['Room Name']=='Room 105 & 106':
                s['Room Name']='Room 105'

            # Breaks?
            if s['Room Name']==' ':
                print( s['Title'] )


        rooms = self.zoo_cages(schedule)
        print(rooms)
        rooms = [r for r in rooms if r not in bad_rooms]
        print(rooms)
        schedule = [s for s in schedule if s['Room Name'] in rooms]

        # some hack to fix a long talk title, I guess.
        # schedule = [s for s in schedule if s['Id'] not in [185,] ]
        # schedule = [s for s in schedule if s['Id'] in [185,] ]
        # schedule[0]['Title']="Security Topics in Open Cloud: Advanced Threats, 2015's Vulnerabilities, Advancements in OpenStack Trusted Computing and Hadoop Encryption"

        schedule = [s for s in schedule
                if s['Title'] not in [
                    'Short break',] ]

        self.add_rooms(rooms,show)

        locs=Location.objects.filter(name__in = bad_rooms)
        for loc in locs:
            loc.active = False
            loc.save()

        events = self.zoo_events(schedule)
        self.add_eps(events, show)

        return


    def pyconau18(self, schedule, show):
        # https://2018.pycon-au.org/schedule/avdata.json

        # emails from super secrete spreadsheet
        presenters = googsheet(
                '1p8BRlUn9sxiAYpZjickb5V_VORbLmMvTOtus233RgIg',
                'veyepar')

        # key on conf id
        presenters = { p['ID']: p for p in presenters }
        # import code; code.interact(local=locals())

        field_maps = [
                ('room','location'),
                ('name','name'),
                ('abstract','description'),
                ('authors','authors'),
                ('','emails'),
                ('twitter_ids','twitter_id'),
                ('reviewers','reviewers'),
                ('start','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('track','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
                ]

        events = self.generic_events(schedule["schedule"], field_maps)

        for event in events:
            if self.options.verbose: pprint(event['raw'])
            if self.options.verbose: pprint(event)

            if "Plenary Hall" in event['location']:
                event['location'] = "Plenary Hall"

            event['name'] =  re.sub( r'[\n\r]', ':)', event['name'] )

            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%dT%H:%M:%S' )

            event['duration'] =   "0:{}:0".format(event['duration'])


            # print(event['authors'])
            if event['authors'] is None:
                event['authors'] =  ''
            else:
                event['authors'] =  ', '.join( event['authors'] )

            event['license'] =  'CC-BY'

            conf_key =  event['conf_key']
            if conf_key in presenters:
                event['emails'] =  (presenters[conf_key]['Email'],)

            if event['emails'] == ["redacted",]:
                event['emails'] =  ""
            else:
                event['emails'] =  ', '.join( event['emails'] )

            if event['conf_url'] is None:
                event['conf_url'] =  ''
            else:
                event['conf_url'] =   event['conf_url'].replace(
                        'https://rego.linux.conf.au', 'http://lca2018.linux.org.au')

            if event['description'] is None:
                event['description'] =  ''

            if event['reviewers'] is None:
                event['reviewers'] =  ''

            event['twitter_id'] = fix_twitter_id(
                    ', '.join(event['twitter_id']))

            if event['conf_key'] == 131 :
                # "name": "Marc Merlin: Getting conned into writing IoTuz/ESP32 drivers and example code (while being held prisoner in a share house in Hobart, Tasmania)"
                print('truncating {} to :168'.format( event['name'] ))
                event['name'] = event['name'][:168]

        rooms = self.get_rooms(events,'location')
        self.add_rooms(rooms,show)
        self.add_eps(events, show)

        return





    def fos_events( self, schedule ):
        # fosdem 14 penta

        events = []
        id = 0

        # schedule[0] is <conference></conference>
        for day in schedule[1:3]:
            # >>> schedule[1].get('date')
            # '2012-02-04'
            start_date = day.get('date')
            print(start_date)
            for room in day:
                for row in room:
                    # >>> event.find('start').text
                    # '10:30'
                    # >>> [x.tag for x in event]
                    """
                    tags = ['start', 'duration', 'room',
                            'slug', 'title', 'subtitle',
                            'track', 'type', 'language',
                            'abstract', 'description',
                            'persons', 'links']
                    for tag in tags:
                        print tag, row.find(tag).text
                    """

                    event={}
                    # event['id'] = row[0]
                    event['name'] = row.find('title').text

                    event['location'] = row.find('room').text

                    dt_format='%Y-%m-%d %H:%M'
                    event['start'] = datetime.strptime(
                            "%s %s" % ( start_date,row.find('start').text),
                            dt_format)

                    event['duration'] = \
                        "%s:00" % row.find('duration').text

                    persons = [p.text for p in
                            row.find('persons').getchildren() ]
                    event['authors'] = ', '.join(persons)

                    event['emails'] = ''
                    event['released'] = True
                    event['license'] = "cc-by"
                    # event['description'] = row.find('description').text
                    # event['description'] = row.find('abstract').text
                    event['description'] = row.find('description').text
                    if event['description'] is None:
                        event['description'] = ''

                    event['conf_key'] = row.get('id')

                    event['conf_url'] = 'https://fosdem.org/2014/schedule/event/%s/' % row.find('slug').text

                    event['tags'] = ''


                    # save the original row so that we can sanity check end time.
                    event['raw'] = row

                    events.append(event)
                    id += 1

        return events


    def fosdem2014(self, schedule, show):

        # top of schedule is:
        # <conference></conference>
        # <day date="2012-02-04" index="1"></day>
        # <day date="2012-02-05" index="2"></day>
        # each day has a list of rooms

        rooms = [ r.get('name') for r in schedule[1] ]


        # remove (foo) stuff from
        # for room in rooms:
        #    room = room.split('(')[0].strip()

        # rooms = set( rooms )
        # probabalby the same rooms the 2nd day.
        # rooms = list(rooms)
        # ['Janson', 'K.1.105', 'Ferrer', 'H.1301', 'H.1302']


        # return

        self.add_rooms(rooms,show)

        # sequance the rooms
        # this will whack any manual edits
        if self.options.update:
            seq = 1
            for room in rooms:
                loc = Location.objects.get(name=room,)
                loc.active=True
                loc.sequence=seq
                loc.save()
                seq+=1

        events = self.fos_events(schedule)

        # no recording in Java room saturday k4201
        events = [ event for event in events if not (
            event['start'].date() != datetime(2014,2,1) and \
                    event['location'] == 'K4201') ]

        self.add_eps(events, show)
        return


    def summit_penta_events( self, schedule ):
        # dc14 summit penta based xml
        # pyconza2015 dc summit penta based xml

        events = []
        id = 0

        # schedule[0] is <conference></conference>
        # for day in schedule[1:3]:
        for day in schedule:
            # >>> schedule[1].get('date')
            # '2012-02-04'
            start_date = day.get('date')
            print(start_date)
            for room in day:
                for row in room:

                    if row.find('persons') is None:
                        continue

                    if self.options.verbose: print(row.get('id'))
                    # import code; code.interact(local=locals())

                    event={}
                    event['name'] = row.find('title').text

                    event['location'] = row.find('room').text

                    dt_format='%Y-%m-%d %H:%M'
                    event['start'] = datetime.strptime(
                            "%s %s" % ( start_date,row.find('start').text),
                            dt_format)

                    event['duration'] = \
                            row.find('duration').text + ":00"


                    persons = []
                    contacts = []
                    twitters = []
                    for p in row.find('persons').getchildren():

                        person = p.text
                        person = person.replace('\n','')
                        # person = person.replace('\r','')
                        person = person.strip()
                        persons.append(person)

                        contact = p.get('contact')
                        if contact not in [
                                None, 'redacted', "<redacted>" ]:
                            contacts.append(contact)

                        twit = p.get('twitter')
                        if twit not in [ None, ]:
                            twitter_id = urllib.parse.urlparse(twit).path[1:]
                            # make sure it starts with an @
                            if not twitter_id.startswith('@'):
                                twitter_id = '@' + twitter_id
                            twitters.append(twitter_id)

                    event['authors'] = ', '.join(persons)
                    event['emails'] = ','.join(contacts)
                    event['twitter_id'] = ' '.join(twitters)
                    event['reviewers'] = ''

                    # (10:59:23 PM) vorlon: CarlFK: I'm pretty sure we never set that field.
                    # event['released'] = row.find('released').text == "True"
                    event['released'] = True

                    # event['license'] = row.find('license').text
                    event['license'] = "CC BY"

                    description = row.find('description').text
                    # if description is None: description = ''
                    description = description.replace('\r','')
                    event['description'] = description

                    event['conf_key'] = row.get('id')

                    # event['conf_url'] = 'https://summit.debconf.org' + row.find('conf_url').text
                    # event['conf_url'] = 'https://za.pycon.org' + row.find('conf_url').text
                    event['conf_url'] = row.find('full_conf_url').text


                    event['tags'] = row.find('track').text

                    # save the original row so that we can sanity check end time.
                    # event['raw'] = row
                    event['raw'] = None

                    # if event['conf_key'] in [ "127", "40"]:
                    # if row.find('slug').text in [ "hacking-time", ]:
                        # skip this one
                        # https://summit.debconf.org/debconf14/meeting/127/hacking-time/
                        # continue

                    events.append(event)
                    id += 1

        return events



    def summit_penta(self, schedule, show):
        # dc14 - summit with penta xml

        # top of schedule is:
        # <conference></conference>
        # <day date="2012-02-04" index="1"></day>
        # <day date="2012-02-05" index="2"></day>
        # each day has a list of rooms

        rooms = [ r.get('name') for r in schedule[2] ]

        print("rooms", rooms)
        self.add_rooms(rooms,show)

        """
        # sequance the rooms
        # this will whack any manual edits
        if self.options.update:
            seq = 1
            for room in rooms:
                loc = Location.objects.get(name=room,)
                loc.active=True
                loc.sequence=seq
                loc.save()
                seq+=1
        """

        events = self.summit_penta_events(schedule)

        self.add_eps(events, show)
        return


    def sched(self,schedule,show):
        # pprint(schedule)

        rooms = self.get_rooms(schedule, "venue")
        self.add_rooms(rooms,show)
        field_maps = [
                ('id','id'),
                ('venue','location'),
                # ('','sequence'),
                ('name','name'),
                # ('','slug'),
                ('speakers','authors'),
                ('','emails'),
                ('description','description'),
                ('event_start','start'),
                ('','duration'),
                ('','released'),
                ('','license'),
                ('','tags'),
                ('event_key','conf_key'),
                ('','conf_url'),
                ('','host_url'),
                ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            if self.options.verbose: print("event", event)
            row = event['raw']

            if 'speakers' not in list(row.keys()):
                # del(event)
                # continue
                pass

            if 'speakers' in list(row.keys()):
                # pprint( row['speakers'] )
                authors = ', '.join( s['name'] for s in row['speakers'] )
            else:
                authors = ''
            event['authors'] = authors
            # print authors

            if 'description' not in list(row.keys()):
                event['description']=''

            start = parse(event['start'])
            end = parse(row['event_end'])

            delta = end - start
            minutes = delta.seconds/60 # - 5 for talk slot that includes break

            duration="00:%s:00" % ( minutes)

            event['start'] = start
            event['end'] = end
            event['duration'] = duration

            # event['released'] = False
            event['released'] = True

            event['license'] =  self.options.license
            # event['tags'] =  ''
            #event['description'] =  ''



        self.add_eps(events, show)

        return


    def pyconde2012(self,schedule,show):
        # pycon 2012 adn 13
        # pprint(schedule)

        rooms = self.get_rooms(schedule )
        self.add_rooms(rooms,show)

        field_maps = [
            ('conf_key','id'),
            ('room','location'),
            ('','sequence'),
            ('name','name'),
            ('','slug'),
            ('authors','authors'),
            ('contact','emails'),
            ('description','description'),
            ('start','start'),
            ('duration','duration'),
            ('released','released'),
            ('license','license'),
            ('tags','tags'),
            ('conf_key','conf_key'),
            ('conf_url','conf_url'),
            ('','host_url'),
            ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:

            if self.options.verbose: print("event", event)
            raw = event['raw']

            event['authors'] =  ', '.join( event['authors'] )
            event['emails'] =  ', '.join( event['emails'] )

            event['start'] = parse(event['start'])
            event['duration'] = "00:%s:00" % ( event['duration'] )

            event['license'] =  ''


        self.add_eps(events, show)

        return

    def pyconca2012(self,schedule,show):
        # pprint(schedule)

        schedule = schedule['data']['talk_list']
        # return talks, session

        # remove rejected talks
        schedule = [t for t in schedule if t['schedule_slot_id'] is not None]

        rooms = self.get_rooms(schedule )
        self.add_rooms(rooms,show)

        field_maps = [
            ('conf_key','id'),
            ('room','location'),
            ('','sequence'),
            ('title','name'),
            ('','slug'),
            ('authors','authors'),
            ('','emails'),
            ('abstract','description'),
            ('start','start'),
            ('duration','duration'),
            ('video_releaase','released'),
            ('','license'),
            ('','tags'),
            ('conf_key','conf_key'),
            ('conf_url','conf_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            if self.options.verbose: print("event", event)
            raw = event['raw']
            if self.options.verbose: pprint(raw)

            event['authors'] = \
              raw['speaker_first_name'] +' ' + raw['speaker_last_name']
            event['emails'] = raw['user']['email']

            event['start'] = datetime.strptime(
                    event['start'],'%Y-%m-%dT%H:%M:%S-05:00')

            event['duration'] = "00:%s:00" % ( event['duration'] )

            event['released'] = raw['video_release']

            event['license'] =  ''


        self.add_eps(events, show)

        return

    def nodepdx(self, schedule, show):
        # Troy's json

        html_parser = html.parser.HTMLParser()

        field_maps = [
            #('','location'),
            # ('','sequence'),
            ('title','name'),
            ('speaker','authors'),
            ('email','emails'),
            ('abstract','description'),
            ('start_time','start'),
            ('end_time','end'),
            ('duration','duration'),
            ('released','released'),
            # ('','license'),
            # ('topics','tags'),
            ('start_time','conf_key'),
            # ('web_url','conf_url'),
            # ('','host_url'),
            # ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        rooms = ['room_1']
        self.add_rooms(rooms,show)

        for event in events:

            # create an ID from day, hour, minute
            event['conf_key'] = \
                event['conf_key'][9] \
                + event['conf_key'][11:13] \
                + event['conf_key'][14:16]

            event['start'] = datetime.strptime(
                    event['start'],'%Y-%m-%d %H:%M:%S')

            event['end'] = datetime.strptime(
                    event['end'],'%Y-%m-%d %H:%M:%S')
            delta = event['end'] - event['start']
            minutes = delta.seconds/60

            duration = int( event['duration'].split()[0] )
            if minutes != duration:
                raise "wtf duration"

            event['duration'] = "00:%s:00" % (duration)

            # Bogus, but needed to pass
            event['location'] = 'room_1'
            event['license'] =  ''

            event['description'] = html_parser.unescape(
                    strip_tags(event['description']) )

            # event['tags'] = ", ".join( event['tags'])
            # pprint(event)

        self.add_eps(events, show)

        return

    def bosc_2014(self, schedule, show):

        # remove rows that have no crowdsource_ref, because spreadsheet
        # schedule = [s for s in schedule if s['Time Start']]
        schedule = [s for s in schedule
                if s['conf_key'] and s['start'] ]

        # convert all the values to unicode strings
        schedule = [{k:d[k].decode('utf-8') for k in d}
                for d in schedule ]

        field_maps = [
            ('conf_key','id'),
            ('conf_key','conf_key'),
            ('room','location'),
            # ('','sequence'),
            ('name','name'),
            ('authors','authors'),
            ('contact','emails'),
            ('description','description'),
            ('start','start'),
            ('end','end'),
            ('','duration'),
            ('released','released'),
            ('license','license'),
            ('tags','tags'),
            ('conf_url','conf_url'),
            # ('','host_url'),
            # ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:

            event['start'] = datetime.strptime(
                    "{0} {1}".format(event['raw']['date'],event['start']),
                    '%d/%m/%Y %H:%M')

            event['end'] = datetime.strptime(
                    "{0} {1}".format(event['raw']['date'],event['end']),
                    '%d/%m/%Y %H:%M')

            delta = event['end'] - event['start']
            minutes = delta.seconds/60
            event['duration'] = "00:{}:00".format(minutes)

            # event['duration'] = "00:{0}:00".format(event['duration'])

            event['released'] = event['released'].lower() == 'y'

        rooms = self.get_rooms(events)
        print(rooms)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

        return


    def depy15(self, schedule, show):

        room = 'Room LL104'

        field_maps = [
                ('title','name'),
                ('start_time','start'),
                ('end_time','end'),
                ('presenter','authors'),
                ('description','description'),
                ('released','released'),
            ]

        events = self.generic_events(schedule, field_maps)
        rooms = [room]
        self.add_rooms(rooms,show)

        for i,event in enumerate(events):
            event['location'] = room
            event['conf_key'] = str(i)

            dt_format='%Y-%m-%d %H:%M'
            event['start'] = datetime.strptime(
                    event['start'], dt_format)

            end = datetime.strptime(
                    event['end'], dt_format)
            seconds=(end - event['start']).seconds
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            event['duration'] =  duration

            if event['description'] is None:
                event['description'] = ''

            event['authors'] = ', '.join(event['authors'].split(' and '))

            event['emails'] = ""
            event['twitter_id'] = ""
            event['license'] = ""
            event['conf_url'] = ""
            event['tags'] = ""

            event['released'] = event['released'] == 'yes'

        self.add_eps(events, show)

        return



    def jupyter_chicago_2016(self, schedule, show):

        room = 'Civis'

        field_maps = [
                ('Talk Title','name'),
                ('start','start'),
                ('duration','duration'),
                ('First Name','authors'),
                # ('Last Name',''),
                ('Twitter Handle','twitter_id'),
                # ('Bio',''),
                # ('Website',''),
                ('Talk Abstract','description'),
                # ('Github Handle',''),
                ('Email','emails'),
                ('Do you give us permission to record and release video of your presentation?','released'),
            ]

        events = self.generic_events(schedule, field_maps)
        rooms = [room]
        self.add_rooms(rooms,show)

        # event_date="February 20th, 2016"
        event_date="2016-02-16"

        for i,event in enumerate(events):
            event['location'] = room
            event['conf_key'] = str(i)

            dt_format='%Y-%m-%d %H:%M'
            event['start'] = datetime.strptime(
                    event_date + ' ' + event['start'], dt_format)

            event['authors'] = \
                    event['authors']+' '+event['raw']['Last Name']

            event['license'] = ""
            event['conf_url'] = ""
            event['tags'] = ""

            event['released'] = event['released'] == 'Yes'

        self.add_eps(events, show)

        return




    def blinkon4(self, schedule, show):

        # remove rows that have no crowdsource_ref, because spreadsheet
        schedule = [s for s in schedule if s['Start Time']]
        # schedule = [s for s in schedule if
        #        s['crowdsource_ref'] or s['released']]

        # convert all the values to unicode strings
        schedule = [{k:d[k].decode('utf-8') for k in d}
                for d in schedule ]

        field_maps = [
            # ('Title Slide Includes BlinkOn 4',''),
            ('Title','name'),
            # ('Notes',''),
            ('Date','start'),
            ('Start Time','start'),
            ('End Time',''),
            # ('Slides',''),
            # ('Internal Video URL',''),
            ('Description for YouTube','description'),
            ('Speaker','authors'),
            ('Should Upload?','released'),
            # ('Good Title Slide',''),
            # ('Shortname',''),
            ]

        events = self.generic_events(schedule, field_maps)
        rooms = ['room 1']
        self.add_rooms(rooms,show)


        for i,event in enumerate(events):
            event['location'] = "room 1"
            event['conf_key'] = str(i)
            # event['authors'] = ', '.join(event['authors'].split(' & '))

            event['start'] = datetime.strptime(
                  event['start'], '%Y/%m/%d %H:%M:%S')
            print(event['start'])

            event['duration'] = "01:00:00"
            event['emails'] = ""
            event['twitter_id'] = ""
            event['license'] = ""
            event['conf_url'] = ""
            event['tags'] = ""

            event['released'] = event['released'] == 'Yes'

        self.add_eps(events, show)

        return




    def wtd_na_2014(self, schedule, show):

        # given a google doc sheet,
        #  export to someting
        #  read in the local file.

        # remove rows that have no crowdsource_ref, because spreadsheet
        # schedule = [s for s in schedule if s['Time Start']]
        schedule = [s for s in schedule if
                s['crowdsource_ref'] or s['released']]

        # convert all the values to unicode strings
        schedule = [{k:d[k].decode('utf-8') for k in d}
                for d in schedule ]

        field_maps = [
            ('key','id'),
            ('Room/Location','location'),
            # ('','sequence'),
            ('Session Title','name'),
            ('','authors'),
            ('Email','emails'),
            ('Description (Optional)','description'),
            ('Time Start','start'),
            # ('Time End','end'),
            ('Length','duration'),
            ('released','released'),
            ('','license'),
            ('tags','tags'),
            ('key','conf_key'),
            ('crowdsource_ref','conf_url'),
            # ('','host_url'),
            # ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)
        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)


        for event in events:

            if " - " in event['name']:
                event['authors'], event['name'] = \
                        event['name'].split(' - ')
                event['authors'] = ', '.join(event['authors'].split(' & '))

            event['start'] = datetime.strptime(
                    "{0} {1}".format(event['raw']['Date'],event['start']),
                    '%m/%d/%Y %H:%M')

            event['duration'] = "00:{0}:00".format(event['duration'])

            event['description'] = event['description'].replace('\n','\r\n')

            event['released'] = event['released'].lower() == 'y'

        self.add_eps(events, show)

        return


    def lanyrd(self, schedule, show):
        # http://lanyrd.com

        field_maps = [
            ('id','id'),
            ('space','location'),
            # ('','sequence'),
            ('title','name'),
            ('speakers','authors'),
            ('twitter','twitter_id'),
            ('email','emails'),
            ('abstract','description'),
            ('start_time','start'),
            ('end_time','end'),
            # ('','duration'),
            # ('','released'),
            # ('','license'),
            ('topics','tags'),
            ('id','conf_key'),
            ('web_url','conf_url'),
            # ('','host_url'),
            # ('','public_url'),
            ]


        rooms = set()
        events =[]
        # flatten out nested json (I think..)
        for day in schedule['sessions']:
            events += self.generic_events(day['sessions'], field_maps)
            # for session in day['sessions']:
                #[u'speakers', u'title', u'event_id', u'start_time', u'space', u'topics', u'times', u'abstract', u'web_url', u'end_time', u'id', u'day']

        # pprint(events[-2])

        # events = [e for e in events if e['location'] is not None]
        # events = [e for e in events if e['start'] is not None]
        # events = [e for e in events
        #        if e['location'] not in ['Hackers Lounge',] ]
        # events = [e for e in events
        #         if e['conf_key'] not in ['sdktrw','sdktrx'] ]


        for event in events:

            if "Lunch" in event['name']:
                event['location']="Main Room"

            if event['location'] is None:
                event['location']="room 1"


            rooms.add(event['location'].lower())

            event['twitter_id'] = " ".join(
                    a['twitter'] for a in event['authors']
                    if a['twitter'] is not None)
            while len(event['twitter_id'])>50: # 135:
                event['twitter_id'] = " ".join(
                        event['twitter_id'].split()[:-1])

            # clobber author object with names.
            event['authors'] = ", ".join(
                    a['name'] for a in event['authors'])

            """
            if event['name'] == "Panel: State of OSS .NET":
                event['twitter_id'] = "@richcampbell @carlfranklin"
                event['authors'] = "Richard Campbell and Carl Franklin"
            """

            event['start'] = datetime.strptime(
                    event['start'],'%Y-%m-%d %H:%M:%S')
            event['end'] = datetime.strptime(
                    event['end'],'%Y-%m-%d %H:%M:%S')
            delta = event['end'] - event['start']
            minutes = delta.seconds/60
            event['duration'] = "00:%s:00" % ( minutes)

            event['description'] = strip_tags(event['description'])


            # if event['location'] is None:
            #    event['location'] = 'room 1'

            event['tags'] = ", ".join( event['tags'])

            # Bogus, but needed to pass
            # event['emails'] = ''
            # event['released'] = bool(event['twitter_id'])
            event['released'] = "*" not in event['name']
            event['license'] =  ''


        # rooms = ['room 1']
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

        return

    def symposion2(self, schedule, show):

        rooms = self.get_rooms(schedule, "room", )
        if self.options.verbose: print(rooms)

        self.add_rooms(rooms,show)

        field_maps = [
            ('conf_key','id'),
            ('room','location'),
            ('name','name'),
            ('authors','authors'),
            ('contact','emails'),
            ('description','description'),
            ('start','start'),
            ('duration','duration'),
            ('released','released'),
            ('license','license'),
            ('kind','tags'),
            ('conf_key','conf_key'),
            ('conf_url','conf_url'),
            # ('twitter_id','twitter_id'),
            ('twitters','twitters'),
            ('reviewer','reviewers'),
           ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            # print event

            raw = event['raw']
            if self.options.verbose: pprint(raw)
            if self.options.verbose: print("event", event)

            event['start'] = datetime.strptime(
                    event['start'],'%Y-%m-%dT%H:%M:%S')

            event['authors'] = ", ".join(event['authors'])

            if event['emails'] == ['redacted']:
                event['emails'] = ''
            else:
                event['emails'] = ", ".join(event['emails'])

            if event['reviewers'] in ['redacted', None]:
                event['reviewers'] = ''
            else:
                # print("event['reviewers']: {reviewers}".format(**event))
                event['reviewers'] = filter(None, event['reviewers'])
                event['reviewers'] = ", ".join(event['reviewers'])
                # if event['reviewers'] == event['emails']:
                #    print('cheater: {} <{}>'.format(
                #        event['authors'], event['emails']))

            if event['twitters'] is None:
                event['twitter_id'] = ""
            else:
                twitters=[]
                for twitter_id in event['twitters']:
                    if twitter_id:
                        # make sure it starts with an @
                        if not twitter_id.startswith('@'):
                                    twitter_id = '@' + twitter_id
                        twitters.append(twitter_id)
                event['twitter_id'] = ' '.join(twitters)

            # if event['duration'] is None: event['duration']=5

            seconds=(int(event['duration'] )) * 60
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            event['duration'] = "%02d:%02d:%02d" % hms

            if event['name']=='Keynote':
                event['name'] = \
                        '%s Keynote - %s' % (
                        self.show.name, event['authors'])
                if not event['description']:
                    event['description']= \
                        'Keynote - %s\n%s\n' % (
                        event['authors'],
                        event['start'].strftime('%A, %B %d %Y %I %p') )

            if event['name'] == "Lightning Talks":
                event['name'] = "%s %s Lightning Talks" % (
                        self.show.name,
                        event['start'].strftime('%A %p') )
                if not event['description']:
                    event['description']= \
                        "%s Lightning Talks\n%s" % (
                        self.show.name,
                        event['start'].strftime('%A, %B %d %Y %I %p') )

        self.add_eps(events, show)

        return

        # If we need short names?
        rooms = {
            'Grand Ballroom AB':'AB',
            'Grand Ballroom CD':'CD',
            'Grand Ballroom EF':'EF',
            'Grand Ballroom GH':'GH',
            'Great America':'Great America',
            'Great America Floor 2B R1':'R1',
            'Great America Floor 2B R2':'R2',
            'Great America Floor 2B R3':'R3',
            'Great America J':'J',
            'Great America K':'K',
            'Mission City':'Mission City',
            'Mission City M1':'M1',
            'Mission City M2':'M2',
            'Mission City M3':'M3',
            'Poster Room':'Poster',
            }


    def pycon2013(self,schedule,show):

        for s in schedule:
            if s['room'] == 'Grand Ballroom GH, Great America, Grand Ballroom CD, Grand Ballroom EF, Grand Ballroom AB, Mission City':
                s['room'] = "Mission City"


        # merge in Zac's poster schedule
        f=open('schedules/postervideo.csv')
        poster_schedule = csv.DictReader(f)
        for poster in poster_schedule:
          conf_key=1000+int(poster['poster_id'])
          for s in schedule:
           if s['kind']=='poster':
            if s['conf_key']==conf_key:

                # set the room to Poster-[1,2,3,4]
                s['room'] = "Poster-%s" % poster['camera']

                # don't care about end, use duration=5
                start,end = poster['time'].split('-')
                h,m = start.split(':')
                s['start'] = datetime(2013, 0o3, 17, int(h), int(m)).isoformat()

        self.symposion2(schedule,show)

        return

    def pydata_2013(self,show):
        print("pydata_2013")
        # f = open('schedules/pydata2013/day1.csv' )
        f = open('schedules/pydata2013/PyData Talks and Speakers.csv', 'rU' )
        schedule = csv.DictReader(f)
        # schedule = list(csv.reader(f))
        # room = "Track %s" % i
        events = []
        pk = 1
        for s in schedule:
            # pprint(s)
            # ['IPython-parallel', ' Min Ragan-Kelley', ' IPython', ' A1', ' 10:45am'],
            # Title,Name,Email,Company,Room,Start,End,Date
            e = { 'conf_key': pk,
                'room':s['Room'].strip(),
                'location':s['Room'].strip(),
                'name':s['Title'],
                'authors':s['Name'].strip(),
                'emails':s['Email'],
                'description':s['Company'].strip(),
                'start':parse(s['Date'] + ' ' + s['Start']),
                'end':parse(s['Date'] + ' ' + s['End']),
                'duration':"0:50:00",
                'released':True,
                'license':"",
                'conf_url':"",
                'tags':'',
                }


            seconds=(e['end'] - e['start']).seconds
            hms = seconds//3600, (seconds%3600)//60, seconds%60
            duration = "%02d:%02d:%02d" % hms
            e['duration'] =  duration

            """
            e = { 'conf_key': pk,
                'room':s[3].strip(),
                'location':s[3].strip(),
                'name':s[0],
                'authors':s[1].strip(),
                'emails':'pwang@continuum.io',
                'description':s[2].strip(),
                'start':parse("Mar 18, 2013" + s[4]),
                'duration':"0:90:00",
                'released':True,
                'license':"",
                'conf_url':"",
                'tags':'',
                }
# 'conf_key':
            """

            # pprint( schedule )
            # pprint( e )
            events.append(e)
            pk +=1

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

    def pyconca2013(self,schedule,show):

        # remvoe the schedule wrapper that protects json
        # from evil list constructors.
        schedule = schedule['schedule']

        # move Pleanary events into the location where the equipment is
        for event in schedule:

            if not event['room']:
                event['room']="None?"

            if "Colony Ballroom" in event['room']:
                event['room']="Colony Ballroom"

        return self.symposion2(schedule,show)


    def pyohio2013(self,schedule,show):

        # remove events with no room (like Break)
        schedule = [s for s in schedule if s['rooms'] ]

        for event in schedule:

            # move Pleanary events into the location where the equipment is
            if "Cartoon 1" in event['room']:
                event['room']="Cartoon 1"

            if "Room 105" in event['room']:
                event['room']="Room 105"

            if 'conf_url' in event:
                if event['conf_url'] is None:
                    event['conf_url'] = 'https://pyohio.org/schedule/'
            else:
                event['conf_url'] = ''

            # if event['license'] == '':
            #    event['license'] = 'CC BY-SA 2.5 CA'

            if event.get('authors') is None:
            #     if "Catherine Devlin" in event['name']:
            #         event['authors'] = ["Catherine Devlin"]
            #     else:
                     event['authors'] = []
                     event['released'] = False

            # elif "&" in event['authors'][0]:
            #     event['authors']=event['authors'][0].split(' & ')

            if ('contact' not in event) or \
                    (event['contact'] is None):
               event['contact'] = []

            if ('reviewer' not in event) or \
                    (event['reviewer'] is None):
               event['reviewer'] = ''

            if 'twitter_id' in event:
               event['twitters'] = [event['twitter_id'],]

            if event.get('description') is None:
               event['description'] = ''



            # if event['name'].startswith('**Opening Remarks:**'):
            #    event['name'] = "Panel Discussion: So You Wanna Run a Tech Conference."
            #    event['authors'] = "Catherine Devlin, Eric Floehr, Brian Costlow, Raymond Chandler, Jason Green, Jason Myers".split(", ")


        return self.symposion2(schedule,show)


    def pytexas2014(self, schedule, show):

        # remove events with no room (like Break)
        # schedule = [s for s in schedule if s['room'] ]

        field_maps = [
            ('id', 'conf_key'),
            ('name', 'name'),
            ('description', 'description'),
            ('duration', 'duration'),
            ('start', 'start'),
            ('room', 'location'),
            ('url', 'conf_url'),
            ('speaker', 'authors'),
            ('speaker', 'emails'),
            ('released', 'released'),
            ('license', 'license'),
            ('language', 'language'),
            ('', 'tags'),
           ]

        events = self.generic_events(schedule, field_maps)

        for event in events:

            event['conf_key'] = str(event['conf_key'])

            if event['location'] == 'all-rooms':
                event['location'] = 'MSC 2300 B'

            event['start'] = datetime.strptime(
                   event['start'], '%Y-%m-%dT%H:%M:%S' )

            event['duration'] = "00:%s:00" % ( event['duration'], )

            if event['authors']['name'] is None:
                event['authors'] = ''
            else:
                event['authors'] =  event['authors']['name']

            if event['emails']['email'] == 'redacted':
                event['emails'] = ''
            else:
                event['emails'] =  event['emails']['email']

            event['released'] = \
                    event['released'] and event['raw']['make_recording']

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

        return

    def erlang_chi_2014(self,schedule,show):

        field_maps = [
            ('room','location'),
            ('','sequence'),
            ('name','name'),
            ('','slug'),
            ('speaker','authors'),
            ('speaker','emails'),
            ('description','description'),
            ('start','start'),
            ('end','end'),
            ('','duration'),
            ('released','released'),
            ('license','license'),
            ('','tags'),
            ('id','conf_key'),
            ('conf_url','conf_url'),
            ('','host_url'),
            ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:

            event['authors'] = event['authors']['name']
            event['emails'] = event['emails']['email']

            event['start'] = datetime.strptime(
                   event['start'], '%Y-%m-%dT%H:%M:%S' )
            event['end'] = datetime.strptime(
                   event['end'], '%Y-%m-%dT%H:%M:%S' )

            delta = event['end'] - event['start']
            minutes = delta.seconds/60
            event['duration'] = "00:%s:00" % ( minutes)

            # event['conf_url'] = "http://www.chicagoerlang.com/{}.html".format(event['conf_key'])

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

        return

    def citycode15(self,schedule,show):

        field_maps = [
            ('room','location'),
                ('title','name'),
                ('speakers','authors'),
                ('speakers','emails'),
                ('speakers','twitter_id'),
                ('start','start'),
            ('end','end'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('tags','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
            ('description','description'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:

            event['authors'] = event['authors'][0]['name']
            event['emails'] = event['emails'][0]['email']
            event['twitter_id'] = event['twitter_id'][0]['twitter_id']

            event['start'] = datetime.strptime(
                   event['start'], '%Y-%m-%dT%H:%M:%S' )
            event['end'] = datetime.strptime(
                   event['end'], '%Y-%m-%dT%H:%M:%S' )

            delta = event['end'] - event['start']
            minutes = delta.seconds/60
            event['duration'] = "00:%s:00" % ( minutes)

            event['released'] =  event['released'] == "yes"


            # event['conf_url'] = "http://www.chicagoerlang.com/{}.html".format(event['conf_key'])

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

        return


    def prodconf14(self,schedule,show):

      field_maps = [
        ('room','location'),
        ('title','name'),
        ('speaker','authors'),
        ('description','description'),
        ('start','start'),
        ('end','end'),
       ]

      events = self.generic_events(schedule, field_maps)

      pk = 1
      for event in events:
        if self.options.verbose:
            print("event:")
            pprint(event)

        event['conf_key'] = "pk{}".format(pk)
        pk += 1

        if event['authors'] is None:
            event['authors'] = ', '.join(
                    [a['name'] for a in event['raw']['speakers']])
        else:
            event['authors'] = event['authors']['name']

        event['emails'] = ''
        event['released'] = False
        event['license'] = False
        event['conf_url'] = ''
        event['tags'] = ''

        event['start'] = datetime.strptime(
               event['start'], '%Y-%m-%dT%H:%M:%S' )
        event['end'] = datetime.strptime(
               event['end'], '%Y-%m-%dT%H:%M:%S' )
        delta = event['end'] - event['start']
        minutes = delta.seconds/60
        event['duration'] = "00:%s:00" % ( minutes)


      rooms = self.get_rooms(events)
      self.add_rooms(rooms,show)

      self.add_eps(events, show)

      return

    def nodevember14(self,schedule,show):

      # remove rows where id='empty'
      schedule = [s for s in schedule if s['id'] != 'empty']

      field_maps = [
              ('room','location'),
              ('name','name'),
              ('speaker','authors'),
              # ('','emails'),
              ('description','description'),
              ('start','start'),
              ('end','end'),
              # ('','duration'),
              ('released','released'),
              ('license','license'),
              # ('','tags'),
              ('id','conf_key'),
              ('conf_url','conf_url'),
       ]

      events = self.generic_events(schedule, field_maps)

      for event in events:
        if self.options.verbose:
            print("event:")
            pprint(event)

        if event['location'] in ["Room 1","Room 2","Room 3","Room 4"]:
            # room 1 is really room 100, 2 200...
            event['location'] = event['location'] + "00"

        speakers = [event['authors']]
        event['authors'] = ', '.join(
                [s['name'] for s in speakers])
        event['emails'] =  ', '.join(
                [s['email'] for s in speakers])

        event['tags'] = ''

        event['start'] = datetime.strptime(
               event['start'], '%Y-%m-%dT%H:%M:%S' )
        event['end'] = datetime.strptime(
               event['end'], '%Y-%m-%dT%H:%M:%S' )
        delta = event['end'] - event['start']
        minutes = delta.seconds/60
        event['duration'] = "00:%s:00" % ( minutes)

        event['conf_url'] = event['conf_url'].replace(".org.com", ".org")


      rooms = self.get_rooms(events)
      self.add_rooms(rooms,show)

      self.add_eps(events, show)

      return

    def osdc2015(self, schedule, show):

        schedule = schedule['schedule']
        schedule = [s for s in schedule if 'authors' in s]

        field_maps = [
                ('room','location'),
                ('name','name'),
                ('description','description'),
                ('authors','authors'),
                ('authors','emails'),
                ('start','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('tags','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
                ('','twitter_id'),
                ('','host_url'),
                ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        # for event in events:
        #    pprint( event )

        # remove events with no room (like Break)
        events = [e for e in events if e['location'] is not None ]

        for event in events:

            if "Derwent 1" in event['location']:
                event['location'] = 'Derwent 1'

            """
            if event['conf_key']==23:
                # name": "Crash-safe Replication with MariaDB...
                event['location'] = 'Riviera'

            if event['conf_key']==20:
                # name": "SubPos...
                event['location'] = 'Derwent 1'

            if event['conf_key']==21:
                # name": "Intro to OpenStreetMap
                event['location'] = 'Derwent 1'

            if event['conf_key']==75:
                # name": "Opportunities in Openness...
                event['location'] = 'Derwent 1'
            """

            event['start'] = datetime.strptime(
                event['start'], '%Y-%m-%dT%H:%M:%S' )

            event['duration'] = "00:{}:00".format(event['duration'])

            event['authors']=', '.join(event['authors'])
            event['emails']=', '.join(event['emails'])

            event['tags'] = ''

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)
        self.add_eps(events, show)

        return

    def nodevember15(self,schedule,show):

      schedule = schedule['schedule']

      s1 = []
      x=1
      for day in schedule:
          date = day["date"]  #: "November 13, 2015",
          for s in day['slots']:
              if "speaker" in s:

                  if s['room'] == "Ezel 301":
                    s['room'] = "Ezell 301"
                  if s['room'] == "Stow 108":
                    s['room'] = "Stowe Hall"

                  s['start'] = "{} {}".format( date, s['time'] )
                  s['duration'] = 60 if s['keynote'] else 40
                  s['key'] = x
                  s['released'] = True
                  x += 1
                  s1.append(s)

      # import code; code.interact(local=locals())

      field_maps = [
              ('room','location'),
              ('title','name'),
              ('speaker','authors'),
              ('','emails'),
              ('summary','description'),
              ('start','start'),
              ('','twitter_id'),
              ('duration','duration'),
              ('released','released'),
              ('','license'),
              ('','tags'),
              ('key','conf_key'),
              ('','conf_url'),
       ]

      # remove rows where id='empty'
      # schedule = [s for s in schedule if s['id'] != 'empty']

      events = self.generic_events(s1, field_maps)

      for event in events:
        if self.options.verbose:
            print("event:")
            pprint(event)

        # event['start'] = dateutil.parser.parse( event['start'] )
        event['start'] = parse( event['start'] )
        # datetime.strptime(
        #       event['start'], '%B %d, %Y %I:%M %p' )


        event['duration'] = "00:{:02}:00".format(event['duration'])

        event['conf_url'] = event['conf_url'].replace(".org.com", ".org")


      rooms = self.get_rooms(events)
      print(rooms)
      self.add_rooms(rooms,show)

      self.add_eps(events, show)

      return

    def nodevember16(self,schedule,show):

      emails={}
      fn = "schedules/Nodevember 2016 Speakers - 2016 Speakers.csv"
      f=open(fn)
      rows = csv.DictReader(f)
      # dict_keys(['First name', 'Email', 'Last name'])
      for row in rows:
          # print(row.keys())
          k = "{First name} {Last name}".format(**row)
          emails[k] = row['Email']

      s1 = []
      for day in schedule:
          date = day["date"]  #: "November 20, 2016"
          for s in day['slots']:
              if s['keynote'] or s['talk']:
                  s['start'] = parse("{} {}".format( date, s['time'] ))
                  s['duration'] = "00:{}:00".format(s['duration'])
                  # s['conf_url'] = urllib.parse.quote(s['conf_url'])
                  s['conf_url'] = s['conf_url'].replace(' ','%20')
                  try:
                      s['emails'] = emails[s['speaker']]
                  except KeyError as e:
                      print(e)
                  s1.append(s)

      field_maps = [
              ('room','location'),
              ('title','name'),
              ('speaker','authors'),
              ('emails','emails'),
              ('description','description'),
              # ('summary','description'),
              ('start','start'),
              ('twitter_id','twitter_id'),
              ('duration','duration'),
              ('released','released'),
              ('license','license'),
              ('','tags'),
              ('conf_key','conf_key'),
              ('conf_url','conf_url'),
       ]

      events = self.generic_events(s1, field_maps)

      rooms = self.get_rooms(events)
      print(rooms)
      self.add_rooms(rooms,show)

      self.add_eps(events, show)

    def djbp10(self, schedule, show):

        room = 'Liberty Hall'

        # make list of talks from dict of talks
        # where video=true
        talks=[]
        for k in schedule['globals']['talks']:
            if schedule['globals']['talks'][k]['video']:
                talks.append( schedule['globals']['talks'][k] )

        field_maps = [
                ('id','conf_key'),
                ('title','name'),
                ('start','start'),
                ('duration','duration'),
                ('speakers','authors'),
                ('abstract','description'),
                ('released','released'),
                ('speakers','twitter_id'),
                ('slug','conf_url'),
            ]

        events = self.generic_events(talks, field_maps)
        rooms = [room]
        self.add_rooms(rooms,show)

        for event in events:
            event['location'] = room

            event['authors'] = ', '.join([
                a['name'] for a in event['authors'] ])

            event['start'] = datetime.strptime(
                    event['start'], '%Y-%m-%dT%H:%M:%S-05:00' )

            event['duration'] = "00:%s:00" % ( event['duration'] )

            try:
                event['twitter_id'] = ', '.join([
                       [ "@"+s['link'].split('/')[-1] for s in t['social']
                       if s['title']=="twitter"][0]
                       for t in event['twitter_id'] ])
            except (IndexError,KeyError) as e:
                event['twitter_id'] = ""

            if event['description'] is None:
                event['description'] = ""


            event['emails'] = ""
            event['license'] = ""
            event['conf_url'] = "https://djangobirthday.com/talks/#{}".format(event['conf_url'])
            event['tags'] = ""


            if self.options.verbose: pprint(event)

        self.add_eps(events, show)

        return


    def pygotham2015(self,schedule,show):

        # PyGotham 2015

        field_maps = [
                # ('id','id'),
                ('room','location'),
                ('title','name'),
                ('user','authors'),
                ('user','emails'),
                ('user','twitter_id'),
                ('description','description'),
                ('start','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('tags','tags'),
                # ('conf_key','conf_key'),
                ('id','conf_key'),
                ('conf_url','conf_url'),
                ('','host_url'),
                ('','public_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        # remove events with no room (like Break)
        events = [e for e in events if e['location'] is not None ]

        for event in events:

            if event['location'] == "Room CR4 & Room CR5 & Room CR6 & Room CR7":
                event['location'] = 'Room CR4'

            # if "701" in event['location']:
            #    event['location'] = 'Room 701'

            # if event['start'] is None:
            #    event['start'] = datetime.now()

            # if event['name'] == "Keynote (JM)":
            #     event['start'] = datetime(2015,8,16,9,0,0)
            # else:

            event['start'] = datetime.strptime(
                event['start'], '%Y-%m-%dT%H:%M:%S' )

            event['duration'] = "00:{}:00".format(event['duration'])

            event['tags'] = ''

            if event['license'] == 'Creative Commons':
                event['license'] = 'CC BY-SA'

            if event['conf_url'] is None:
                # URL base is now https://2016.pygotham.org/talks/
                # base = 'https://pygotham.org/2015/'
                base = 'https://2016.pygotham.org'
                event['conf_url'] = '{base}/talks/{id}/{slug}'.format(
                    base=base,
                    id = event['conf_key'],
                    slug = slugify(event['name']) )

                # https://pygotham.org/2015/talks/169/going-parallel-and-out-of

            # event['authors']=', '.join(event['authors'])
            event['authors']=event['authors']['name']

            if event['emails']['email']=="<redacted>":
                event['emails']=""
            else:
                event['emails']=event['emails']['email']

            if event['twitter_id']['twitter_id']:
                event['twitter_id']="@" + event['twitter_id']['twitter_id']
            else:
                event['twitter_id']=""


        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)


    def kiwipycon2015(self,schedule,show):

        field_maps = [
                # ('id','id'),
                ('room','location'),
                ('name','name'),
                ('authors','authors'),
                ('contact','emails'),
                ('abstract','description'),
                ('start','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('tags','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
                ('','twitter_id'),
            ]

        events = self.generic_events(schedule, field_maps)

        # remove events with no room (like Break)
        # events = [e for e in events if e['location'] is not None ]

        for event in events:

            event['start'] = datetime.strptime(
                event['raw']['date'] + 'T' + event['start'],
                '%d/%m/%YT%H:%M:%S' )

            event['duration'] = "00:{}:00".format(event['duration'])

            if event['license'] == 'CC':
                event['license'] = 'CC BY-SA'

            event['authors']=', '.join(event['authors'])
            event['emails']=', '.join(event['emails'])


        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)



    def linuxwochen(self,schedule,show):

        conf = schedule['schedule']['conference']

        schedule = []
        for day in conf['days']:
            for room in day['rooms']:
                for event in day['rooms'][room]:
                    if self.options.verbose: pprint(event)
                    schedule.append(event)

        field_maps = [
                # ('id','id'),
                ('room','location'),
                ('title','name'),
                ('persons','authors'),
                ('','emails'),
                ('description','description'),
                ('date','start'),
                ('duration','duration'),
                # ('released','released'),
                # ('license','license'),
                ('track','tags'),
                ('language','language'),
                ('id','conf_key'),
                ('id','conf_url'),
                ('','twitter_id'),
            ]
        # https://cfp.linuxwochen.at/de/LWW16/public/events/396

        events = self.generic_events(schedule, field_maps)

        # remove events with no room (like Break)
        # events = [e for e in events if e['location'] is not None ]

        for event in events:
            if self.options.verbose: pprint(event)

            event['conf_key']=str(event['conf_key'])

            event['conf_url']="https://cfp.linuxwochen.at/de/LWW16/public/events/{}".format(event['conf_key'])

            event['start'] = datetime.strptime(
                event['start'],
                '%Y-%m-%dT%H:%M:%S+02:00' )

            event['duration'] = "{}:00".format(event['duration'])


            event['authors']=', '.join([
                p['full_public_name'] for p in event['authors']])

            event['released']=False
            event['license'] = 'CC BY-SA'


        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)



    def amberapp(self,schedule,show):

        schedule = schedule['speaker_list']

        field_maps = [
                # ('id','id'),
                ('room','location'),
                ('title','name'),
                ('presenter_list','authors'),
                ('presenter_list','emails'),
                ('presenter_list','twitter_id'),
                ('description','description'),
                ('start_time','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('','tags'),
                ('talk_language','language'),
                ('id','conf_key'),
                ('conf_url','conf_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        # remove events with no room (like Break)
        # events = [e for e in events if e['location'] is not None ]

        for event in events:
            if self.options.verbose: pprint(event)

            event['conf_key']=str(event['conf_key'])

            event['start'] = datetime.strptime(
                event['start'],
                '%Y-%m-%d %H:%M:%S' )

            event['duration'] = "{}:00".format(event['duration'])


            event['authors']=', '.join(
                [ d[list(d.keys())[0]]['name'] for d in event['authors']])

            event['twitter_id']=', '.join(
                [ d[list(d.keys())[0]]['twitter_id'] for d in event['twitter_id']])

            event['emails']=', '.join(
                [ d[list(d.keys())[0]]['email'] for d in event['emails']])



        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)

    def nzpug(self,schedule,show):

        field_maps = [
                ('room','location'),
                ('name','name'),
                ('authors','authors'),
                ('contact','emails'),
                ('description','description'),
                # ('abstract','description'),
                ('','twitter_id'),
                ('{date} {start}','start'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('tags','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            if self.options.verbose: pprint(event)

            event['conf_key']=str(event['conf_key'])

            event['start'] = datetime.strptime(
                event['start'], '%d/%m/%Y %H:%M:%S' )

            event['duration'] = "{}:00".format(event['duration'])

            event['authors']=', '.join( event['authors'] )

            event['emails']=', '.join( event['emails'] )

            event['reviewers']=''


        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)


    def koya(self, schedule, show):
        # open .docx in OO, File/SaveAs foo.txt
        key=0
        start=datetime(2018,7,8,9,0,0)
        events = []
        for s in schedule:
            print(s)

            name = s.strip()
            # name = s['\ufefftitle'],

            if len(name)==0:
                # skip blank lines
                # pass
                continue

            # print("{} - {}".format(len(name), name.__repr__()))

            event = {
                'location': 'Room 1',
                'name': name,
                'authors': 'Devi Koya',
                'start': start,
                'duration': '15:00',
                'conf_key':key,
                'conf_url':'',
                'emails':'',
                'twitter_id':'',
                'reviewers':'',
                'description':'',
                'tags':'',
                'released':True,
                'license':'',
                }

            events.append(event)
            key+=1
            start+=datetime.timedelta(minutes=10)
            # lunch break
            # if start==datetime(2018,4,21,12,0,0):
            #    start+=datetime.timedelta(hours=1)

        self.add_eps(events, show)



    def dnf(self,schedule,show):

        # pull in data from Troy's goog sheet
        talks={}
        for d in [1,2]:
            fn = "schedules/dnf16d{}.csv".format(d)
            f=open(fn)
            rows = csv.DictReader(f)
            for row in rows:
                if row['Lanyrd Link']:
                    conf_key = str(row['Lanyrd Link']).split('/')[-2]
                    talks[conf_key] = row

        fn = "schedules/dnf_lighning_talks.txt"
        f=open(fn)
        for line in f.read().split('\n'):
            print(line)
            # by Andrea Goulet Ford
            if line.startswith('by'):
                speaker=line[3:]
            elif line.startswith('Lightning'):
                title=line
            elif line.startswith('http://lanyrd.com'):
                conf_key = line.split('/')[-2]
                talks[conf_key] = {
                        'Speaker':speaker,
                        'Email':''}

        events=[]
        for component in schedule.walk():
            if component.name == "VEVENT":

                event={}

                event['name'] = str(component.get('summary'))
                if "Lighting" in event['name']: continue

                s = component.get('dtstart')
                start = s.from_ical(s) - datetime.timedelta(hours=7)
                print(s,start)
                # event['start'] = localtime(start) #.replace(tzinfo=None)
                print("import sys;sys.exit()"); import code; code.interact(local=locals())
                try:
                    event['start'] = start.replace(tzinfo=None)
                except TypeError:
                    continue

                e = component.get('dtend')
                end = e.from_ical(e) - datetime.timedelta(hours=7)
                event['end'] = end.replace(tzinfo=None)

                delta = end - start
                minutes = delta.seconds/60 # - 5 for talk slot that includes break

                event['duration'] = "00:%s:00" % ( minutes)

                l = component.get('location')
                event['location'] = str(l)

                k =  component.get('URL')
                event['conf_url'] = str(k)
                event['conf_key'] = str(k).split('/')[-2]

                if event['conf_key'] in talks:
                    event['authors']=talks[event['conf_key']]['Speaker']
                    event['emails']=talks[event['conf_key']]['Email']
                else:
                    event['authors']=''
                    event['emails']=''

                event['twitter_id']=''
                event['description'] = str(component.get('description'))
                event['tags']=''

                event['released']=True
                event['license']='CC-BY'

                event['raw']=''

                print( event )
                events.append(event)

                pprint(component)

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)


    def ical(self,schedule,show):

        events=[]
        for component in schedule.walk():
            if component.name == "VEVENT":
                # pprint(component)

                event={}

                event['name'] = str(component.get('summary'))

                s = component.get('dtstart')
                start = s.from_ical(s)
                event['start'] = start

                e = component.get('dtend')
                end = e.from_ical(e)
                event['end'] = end

                delta = end - start
                minutes = int(delta.seconds/60) # - 5 for talk slot that includes break
                event['duration'] = "00:%s:00" % ( minutes)

                l = component.get('location')
                event['location'] = str(l)

                k =  component.get('URL')
                event['conf_url'] = str(k)

                # pprint( event )
                events.append(event)

        return events


    def osem(self,schedule,show):

        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        def one_page(url):
	    # resp =  requests.get('https://postgresconf.org/conferences/SouthAfrica2018/program/proposals/face-recognition-and-postgres', verify=False)
            resp =  requests.get(url, verify=False)
            doc = html.document_fromstring(resp.text)
            el = doc.get_element_by_id('proposal-info')
            data = dict(zip(
                (e.text.strip() for e in el[::2]),
                (e.text.strip() for e in el[1::2])
                ))
            data['meta title'] = doc.xpath('//meta[@property="og:title"]')[0].get('content')
            data['meta description'] = doc.xpath('//meta[@property="og:description"]')[0].get('content')
            desc = doc.xpath('.//div[contains(@class, "page-header")]//div[contains(@class, "row")]//small')
            data['html description'] = desc[0].text.strip() if desc else ''

            data['html user'] = doc.xpath('.//a[contains(@href,"user")]')[0].text

            # pprint(data)
            return data


        def add_csv(events, csv_name):

            f=open(csv_name)
            rows = csv.DictReader(f)
            # print("import sys;sys.exit()"); import code; code.interact(local=locals())
            for row in rows:
                event = [e for e in events if e['conf_key'] == row['Event ID']][0]
                event['emails'] = row['Email']

            return events


        events = self.ical(schedule,show)

        for event in events:

            event['conf_key'] = event['conf_url'].split('/')[-1]
            page = one_page( event['conf_url'] )

            event['name']= page['meta title']
            event['authors']= page['html user']

            event['location']= page['Room:']
            event['description'] = page['html description']


            event['start']=event['start'].replace(tzinfo=pytz.timezone("Africa/Johannesburg"))
            event['end']=event['end'].replace(tzinfo=pytz.timezone("Africa/Johannesburg"))

            event['start']=event['start'].replace(tzinfo=None)
            event['end']=event['end'].replace(tzinfo=None)
            event['start']=event['start'] + datetime.timedelta(hours=2)
            event['end']=event['end'] + datetime.timedelta(hours=2)

            event['emails']=''
            event['reviewers']=''

            event['twitter_id']=''
            event['tags']=''

            event['released']=True
            event['license']='CC-BY'

            event['raw']=''

            # pprint(event)

        events = add_csv(events, "schedules/pgconf_events.csv")

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)


        return


    def teardown18(self,show):

        schedule = googsheet(
                '1ZS6VFOLV8kaa_VSwrf0tt5wIbaEtXlKhahOtxdR3RAM')
        # ['presenter', 'email', 'city', 'title', 'description', 'bio', 'notes', 'duration', 'start', 'room', 'released', 'conf_key', 'reviewer']
        # ['presenter', 'email', 'title ', 'description', 'Format', 'Day', 'Time START', 'Time END', 'DUR. (h)', 'Room / Location', 'Format (REQUESTED)', 'Speaker Handle(s)', 'released', 'conf_key', 'reviewer']

        schedule = [ s for s in schedule
                if 'conf_key' in s and s['conf_key']]
        schedule = [ s for s in schedule if s['Time START']]

        field_maps = [
                ('Room / Location','location'),
                ('title','name'),
                ('presenter','authors'),
                ('email','emails'),
                ('description','description'),
                # ('abstract','description'),
                ('Speaker Handle(s)','twitter_id'),
                ('{Day} {Time START}','start'),
                ('DUR. (h)','duration'),
                ('released','released'),
                # ('','license'),
                # ('tags','tags'),
                ('conf_key','conf_key'),
                ('reviewer','reviewers'),
                ('','conf_url'),
                ('','tags'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            if self.options.verbose: pprint(event)

            day,start = event['start'].split(' ',1)
            day = {'FRI': 11,
                    'SAT': 12,
                    'SUN': 13}[day]
            dt = '5/{day}/2018 {start}'.format(day=day,start=start)
            event['start'] = datetime.strptime(
                dt, '%m/%d/%Y %I:%M %p' )

            """
            # Talk (60 minutes)
            re_duration = re.compile(r"(Talk|Workshop) \((?P<qty>[\d\-]+) (?P<unit>(hours|minutes))\)")
            try:
                duration = re.match( re_duration, event['duration'] ).groupdict()
            except:
                print(event['duration'])
                print(re_duration)

            pprint(duration)
            if duration['unit'] == 'minutes':
                event['duration'] = "{}:00".format(duration['qty'])
            else:
                continue
            """
            event['duration'] = "{}:00".format(event['duration'].strip())

            if not event['twitter_id'].startswith('@'):
                event['twitter_id']=''

            if event['reviewers'] is None:
                event['reviewers']=''

            event['released'] = event['released'].lower() == 'yes'

            event['license'] = 'CC BY-SA'

        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)


    def emwc(self, show, response):


        fields = ['conf_key', 'start', 'duration', 'name', 'authors', 'twitter_id', 'emails', 'reviewer', 'released', 'conf_url', 'license']

        parsed = urllib.parse.urlparse(response.url)
        # print("import sys;sys.exit()"); import code; code.interact(local=locals())
        www = "{scheme}://{netloc}".format(
                scheme = parsed.scheme,
                netloc = parsed.netloc,
                )

        emails = {
                'Comunity': '',
                'to be announced': '',
                }
        for line in open( os.path.join( self.show_dir,
            "meta", "emails.txt")).read().split('\n'):
            name = ' '.join(line.split()[:-1])
            emails[name] = line

        i=1
        talks = []

        soup = BeautifulSoup(response.content, "html.parser")

        # node = soup.find(id="Program")
        # t1 = node.find_next('table')

        sched_head_re = re.compile("Conference Day [12].*")
        for node in soup.find_all(string = sched_head_re):
            _, start_date = node.split(' - ')
            start_date = start_date.strip()
            t = node.find_previous('table')
            trs = t.find_all('tr')
            for tr in trs:
                tds = tr.find_all('td')
                if len(tds) == 1:
                    continue
                lis = tds[2].find_all('li')
                # if there is a list of talks:
                if lis:
                    start_time, end = tds[0].text.split(' - ')
                    # ['9:00 AM', '10:30 AM\n']
                    start_dt = start_date + 'T' + start_time
                    # 'Wednesday, April 3, 2019'
                    start = datetime.strptime(start_dt,
                            '%A, %B %d, %YT%I:%M %p')
                    for li in lis:
                        url = ""
                        if li.text == 'TBD':
                            continue
                        elif li.text == 'Lightning Talks':
                            title = li.text
                            authors = "Comunity"
                        elif li.find(string="Panel"):
                            title = "Panel: State of the MediaWiki Ecosystem"
                            authors = "Daren Welsh"
                        elif li.next == 'Moderator: ':
                            # import pdb; pdb.set_trace()
                            break
                        else:
                            ahrefs = li.find_all('a')
                            if len(ahrefs) == 2:
                                url = www + ahrefs[0].get('href')
                                # session = requests.session()
                                # response = session.get(show.schedule)
                            try:
                                title, authors = li.text.split(' - ')
                            except:
                                print("import sys;sys.exit()"); import code; code.interact(local=locals())



                        time_re = re.compile(
                                "(?P<authors>.*) \((?P<mins>\d+) (?P<units>minutes|hour)\)")
                        match = time_re.match(authors)
                        if match:
                            mins = int(time_re.match(authors).group('mins'))
                            authors = time_re.match(authors).group('authors')
                        else:
                            mins = 30
                        duration = "00:{}:00".format(mins)

                        email = emails[authors]

                        talk = {
                                'conf_key': i,
                                'location': 'Genesys',
                                'start': start,
                                'duration': duration,
                                'name': title,
                                'authors': authors,
                                'twitter_id': '',
                                'emails': email,
                                'reviewers': '',
                                'released': None,
                                'conf_url': url,
                                'license': 'CC-BY-NA',
                                'description': '',
                                'tags': '',
                                }

                        talks.append(talk)
                        # if authors == 'Clément Flipo':
                        #    print("import sys;sys.exit()"); import code; code.interact(local=locals())

                        i += 1
                        start += timedelta(minutes = mins)


        talk = {
            'conf_key': 100,
            'location': 'Genesys',
            'start': datetime(2019,4,4,9,00,00),
            'duration': "1:00:00",
            'name': "Keynote: Wikidata and Beyond",
            'authors': "Denny Vrandečić",
            'twitter_id': '',
            'emails': '',
            'reviewers': '',
            'released': None,
            'conf_url':
                www + '/wiki/EMWCon_Spring_2019/Wikidata_and_Beyond',
            'license': 'CC-BY-NA',
            'description': '',
            'tags': '',
            }
        talk['email'] = emails[talk['authors']]
        talks.append(talk)


        with open(self.show_dir+"/sched.csv",'w') as f:
            dw = csv.DictWriter(f, fields)
            for talk in talks:
                d = {}
                for k in talk:
                    if k in fields:
                        d[k] = talk[k]
                # d = { (k,v) for k,v in talk if k in fields }
                dw.writerow(d)

        rooms = self.get_rooms(talks)
        self.add_rooms(rooms,show)

        self.add_eps(talks, show)




    def lcza(self, schedule, show):

        schedule = [ s for s in schedule if s['speakers'] is not None]

        field_maps = [
                ('room','location'),
                ('title','name'),
                ('speakers','authors'),
                ('speakers','emails'),
                ('speakers','twitter_id'),
                ('reviewers','reviewers'),
                ('start','start'),
                ('end','end'),
                ('duration','duration'),
                ('released','released'),
                ('license','license'),
                ('language',''),
                ('tags','tags'),
                ('conf_key','conf_key'),
                ('conf_url','conf_url'),
                ('summary','summary'),
                ('description','description'),
            ]

        events = self.generic_events(schedule, field_maps)

        for event in events:
            if self.options.verbose: pprint(event)

            # "start": "2018-10-08 09:20",
            event['start'] = datetime.strptime(
                    event['start'],'%Y-%m-%d %H:%M')
            event['end'] = datetime.strptime(
                    event['end'],'%Y-%m-%d %H:%M')

            event['duration'] = "{}:00".format(event['duration'])

            event['released'] = event['released'].lower() == 'yes'

            event['authors'] = ", ".join(
                    a['name'] for a in event['authors']
                    if a['name'] is not None)

            event['emails'] = ", ".join(
                    a['email'] for a in event['emails']
                    if a['email'] is not None)

            event['twitter_id'] = " ".join(
                    a['twitter_id'] for a in event['twitter_id']
                    if a['twitter_id'] is not None)
            while len(event['twitter_id'])>50: # 135:
                event['twitter_id'] = " ".join(
                        event['twitter_id'].split()[:-1])

            if event['description'] is None:
                event['description'] = ''

            if event['summary'] is not None:
                event['description'] += event['summary']


        rooms = self.get_rooms(events)
        self.add_rooms(rooms,show)

        self.add_eps(events, show)


#################################################3
# main entry point

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
        """
            'djangocon2011': 'http://djangocon.us/schedule/json/',
            'pygotham_2012': 'http://pygotham.org/talkvote/full_schedule/',
            'pytexas_2011': 'http://www.pytexas.org/2011/schedule/json/',
            'pyconde2011': 'http://de.pycon.org/2011/site_media/media/wiki/mediafiles/pyconde2011_talks.json',
            'ddu_2012': "http://drupaldownunder.org/program/session-schedule/json",
            'lca_2012': "http://lca2012.linux.org.au/programme/schedule/json",
            'fosdem_2012': "http://tmp.fosdem.org/video.xml",
            'pycon_2012': "https://us.pycon.org/2012/schedule/json/",
            'xpycon_2012': "file://pc2012.json",
            'flourish_2012': "http://flourishconf.com/2012/schedule_json.php",
            'chipy_may2012': "http://72.14.188.25:8095/meetings/1/topics.json",
            'ictev_2012': "http://ictev.vic.edu.au/program/2012/json",
            # 'ictev_2013': "http://ictev.vic.edu.au/program/2013/json",
            'ictev_2013': "file://schedules/ictev2013.json",
            # 'scipy_2012_v1': "file://scipy_talks.json",
            # 'scipy_2012_v2': "http://conference.scipy.org/scipy2012/talks/test.php",
            # 'scipy_2012': "http://conference.scipy.org/scipy2012/talks/schedule_json.php",
            'scipy_2012': "http://conference.scipy.org/scipy2012/schedule/schedule_json.php",
            'chipy_june2012': "http://chipy.org/api/meetings/",
            'chipy_july_2012': "http://chipy.org/api/meetings/",
            'pyohio_2012': "file://pyohio_2012.json",
            'chipy_aug_2012': "http://chipy.org/api/meetings/",
            'pycon_au_2012': "http://2012.pycon-au.org/programme/schedule/json",
            'chipy_sep_2012': "http://chipy.org/api/meetings/",
            'chipy_jan_2013': "http://chipy.org/api/meetings/",
            'chipy_feb_2013': "http://chipy.org/api/meetings/",
            # 'pyconde2012': 'http://de.pycon.org/2011/site_media/media/wiki/mediafiles/pyconde2011_talks.json',
            # 'pyconde2012': 'https://stage.2012.de.pycon.org/episodes.json',
            'pyconde2012': 'https://2012.de.pycon.org/episodes.json',
            'pyconca2012': 'http://pycon.ca/talk.json',
            'lca2013': 'http://lca2013.linux.org.au/programme/schedule/json',
            'pycon2013': 'https://us.pycon.org/2013/schedule/conference.json',
            'write_the_docs_2013': 'file://schedules/writethedocs.json',
            # 'write_the_docs_2013': 'http://lanyrd.com/2013/writethedocs/schedule/ad9911ddf35b5f0e.v1.json',
            'nodepdx2013': 'file://schedules/nodepdx.2013.schedule.json',
            'chipy_may_2013': "http://chipy.org/api/meetings/",
            }[self.options.show]
            """

        client = show.client
        self.set_dirs(show)
        url = show.schedule_url
        if self.options.verbose: print(url)

        if self.options.client =='croud_supply':
            return self.teardown18(show)

        if url.startswith('file'):
            f = open(url[7:])
            # j = f.read()
        else:

            session = requests.session()
            headers = {}

            # auth stuff goes here, kinda.

            auth = pw.addeps.get(self.options.client, None)

            if auth is not None:
                if self.options.verbose: print(auth)

                headers = auth.get('headers', {})

                if 'login_page' in auth:

                    # get the csrf token out of login page
                    session.get(auth['login_page'])
                    token = session.cookies['csrftoken']


                    # in case it does't get passed in the headers
                    # result = requests.get(auth['login_page'])
                    # soup = BeautifulSoup(x.text)
                    # token = soup.find('input',
                    #        dict(name='csrfmiddlewaretoken'))['value']


                    # setup the values needed to log in:
                    login_data = auth['login_data']
                    login_data['csrfmiddlewaretoken'] = token

                    if self.options.verbose: print("login_data", login_data)

                    headers['Referer']=auth['login_page']

                    ret = session.post(auth['login_page'],
                            data=login_data,
                            headers=headers)

                    if "sessionid" in session.cookies:
                        print("login successful")
                    else:
                        print('"sessionid" not in session.cookies')

                    if self.options.verbose: print("login ret:", ret)


            if self.options.show in ['chicagowebconf2012"',
                                        "cusec2013" , ]:
                payload = {
                    "api_key": pw.sched[self.options.show]['apikey'],
                    "format":"json",
                    # "fields":"name,session_type,description",
                    "strip_html":"Y",
                    "custom_data":"Y",
                    }

            else:
                payload = None

            pprint(headers)
            # return

            for x in 1, : #,2:
                response = session.get(url, params=payload, verify=False,
                    headers=headers)

            if self.options.client =='emwc':
                return self.emwc(show, response)


        parsed = urllib.parse.urlparse(url)
        ext = os.path.splitext(parsed.path)[1]
        if ext=='.csv':
            # schedule = list(csv.reader(f))
            schedule = list(csv.DictReader(f))
            if 'desktopsummit.org' in url:
                return self.desktopsummit(schedule,show)

        elif ext=='.xml':

          if url.startswith('file'):
            schedule=xml.etree.ElementTree.XML(f.read())
          else:
            schedule=xml.etree.ElementTree.XML(
                    response.content)

        elif ext=='.ics' or url.endswith('ical'):
            schedule=Calendar.from_ical(response.content)
            # schedule=Calendar.from_ical(f.read())

        elif ext=='.txt':
            schedule = f

        else:
            # lets hope it is json, like everything should be.

            if url.startswith('file'):
                j = f.read()
                schedule = json.loads(j)
                # schedule = json.loads(f.read())
            else:
                j = response.text
                print( j[:30].__repr__() )
                schedule = response.json()

            # if it is a python prety printed list:
            # (pyohio 2012)
            # schedule = eval(j)

        # save for later
        # filename="schedule/%s_%s.json" % ( client.slug, show.slug )
        # file(filename,'w').write(j)
        # j=file(filename).read()

        if self.options.verbose: pprint(schedule)

        # if self.options.verbose: print j[:40]
        if self.options.keys: return self.dump_keys(schedule)

        # look at fingerprint of file, (or cheat and use the showname)
        #   call appropiate parser

        if url.endswith('programme/schedule/json'):
            # Zookeepr
            return self.zoo(schedule,show)

        if url.endswith('/schedule_json.php'):
            # LinuxConf ZA 2018
            return self.lcza(schedule,show)

        if ext =='.ics':
            return self.ics(schedule,show)

        if self.options.client =='emwc':
            return self.emwc(schedule, show)

        if self.options.client =='koya_law':
            return self.koya(schedule, show)

        if self.options.client =='pgza':
            return self.osem(schedule,show)

        if self.options.show =='pyconau_2018':
            return self.pyconau18(schedule, show)

        if self.options.client =='kiwipycon':
            return self.nzpug(schedule,show)

        if self.options.show =='depy_2016':
            return self.amberapp(schedule,show)

        if self.options.show =='linuxwochen_wien_2016':
            return self.linuxwochen(schedule,show)

        if self.options.show =='osdc2015':
            return self.osdc2015(schedule,show)

        if self.options.show =='djbp10':
            return self.djbp10(schedule,show)

        if self.options.show =='nodevember16':
            return self.nodevember16(schedule,show)

        if self.options.show =='nodevember15':
            return self.nodevember15(schedule,show)

        if self.options.show =='nodevember14':
            return self.nodevember14(schedule,show)

        if self.options.show =='prodconf14':
            return self.prodconf14(schedule,show)

        if self.options.show =='kiwipycon2015':
            # return self.veyepar(schedule,show)
            return self.kiwipycon2015(schedule,show)

        if self.options.show =='citycode15':
            return self.citycode15(schedule,show)

        if self.options.show =='chicago_erlang_factory_lite_2014':
            return self.erlang_chi_2014(schedule,show)

        if self.options.show =='pytexas2014':
            return self.pytexas2014(schedule,show)

        if self.options.show in ['pyconza2015', 'pyconza2016', 'pyconza2018']:
            return self.summit_penta(schedule,show)

        if self.options.show =='debconf17':
            return self.summit_penta(schedule,show)

        if self.options.show =='bosc_2014':
            return self.bosc_2014(schedule,show)

        if self.options.show =='wtd_NA_2014':
            return self.wtd_na_2014(schedule,show)

        if self.options.client =='fosdem':
            return self.fosdem2014(schedule,show)

        if self.options.client =='chipy':
            return self.chipy_v3(schedule,show)

        if self.options.show =='nodepdx2013':
            return self.nodepdx(schedule,show)

        if url.startswith("http://lanyrd.com"):
        # if self.options.show =='write_the_docs_2013':
        # if self.options.show =='write_the_docs_2016':
            return self.lanyrd(schedule,show)

        if self.options.show =='write_docs_na_2016':
            # for Eric's email me a file process
            return self.lanyrd(schedule,show)

        if self.options.show in [
                'pyohio_2016','pyohio_2015',"pycon_2014_warmup",
                'pyohio_2017', ]:
            return self.pyohio2013(schedule,show)

        if self.options.show in [
            'pycon_au_2017']:
            schedule = schedule['schedule']
            return self.pyohio2013(schedule,show)

        if self.options.show =='pygotham_2016':
            return self.pygotham2015(schedule,show)

        if self.options.show =='pyconca2013':
            return self.pyconca2013(schedule,show)

        if self.options.show =='pytn2014':
            return self.pyconca2013(schedule,show)

        if self.options.show =='pyconca2012':
            return self.pyconca2012(schedule,show)

        if self.options.show == 'pyconde2013':
            # "same as last year"
            return self.pyconde2012(schedule,show)

        if self.options.show == 'pyconde2012':
            return self.pyconde2012(schedule,show)

        if self.options.show == 'pycon2013':
            return self.pycon2013(schedule,show)

        # if self.options.show =='chicagowebconf2012':
        if url.endswith(".sched.org/api/session/export"):
            # Sched.org Conference Mobcaile Apps
            # Chicago Web Conf 2012
            return self.sched(schedule,show)

        if self.options.show == 'pyohio_2012':
            # pyohio
            return self.pyohio(schedule,show)

        if self.options.show == 'scipy_2012':
            # scipy ver 2
            return self.scipy_v2(schedule,show)

        if self.options.show == 'scipy_2012_v1':
            # scipy ver 1
            return self.scipy_v1(schedule,show)

        if self.options.client == 'chipy':
            # chipy
            return self.chipy_v1(schedule,show)

        if self.options.show == 'flourish_2012':
            # flourish_2012
            return self.flourish(schedule,show)

        if self.options.show == 'pyconde2011':
            # pycon.de 2011
            return self.pyohio(schedule,show)
            # return self.pyconde2011(schedule,show)

        if self.options.show =='blinkon4':
            return self.blinkon4(schedule,show)

        if self.options.show =='depy_2015':
            return self.depy15(schedule,show)

        if self.options.show =='jupyter_chicago_2016':
            return self.jupyter_chicago_2016(schedule,show)

        if j.startswith('{"schedule": [{"') or \
                j.startswith('{\n  "schedule": [\n    {\n      '):
            print("symposion_chrisjrn")
            # {"schedule": [{"tags": "", "co
            # lca 2017
            # NBPY
            # PyOhio 2018
            # lca 2019
            return self.symposion_chrisjrn(schedule,show)

        if j.startswith('{"files": {'):
            # doug pycon, used by py.au
            return self.pctech(schedule,show)

        if j.startswith('[{"pk": '):
            # veyepar show export
            return self.veyepar(schedule,show)

        if j.startswith('[{"') and 'room_name' in schedule[0]:
            # PyCon 2012
            return self.symposium(schedule,show)

        if j.startswith('[{"') and 'last_updated' in schedule[0]:
            # pyohio
            return self.pyohio(schedule,show)

        if j.startswith('[{"') and 'start_iso' in schedule[0]:
            # pyTexas
            return self.pyohio(schedule,show)

        if j.startswith('[{"') and 'talk_day_time' in schedule[0]:
            # pyGotham
            return self.pygotham(schedule,show)

        if url.endswith('/program/2012/json'):
            # some drupal thing
            # 'ictev_2012': "http://ictev.vic.edu.au/program/2012/json",

            # dig out the data from the nodes:[data]
            schedule = [s['node'] for s in schedule['nodes']]
            # pprint( schedule )

            return self.ictev(schedule,show)

        if self.options.show == 'ictev_2013':
            # some drupal thing
            # 'ictev_2013': "http://ictev.vic.edu.au/program/2013/json",

            schedule =  self.unfold_origami_unicorn( schedule )
            # pprint( schedule )
            # return self.dump_keys(schedule)

            return self.ictev_2013(schedule,show)


        if url.endswith('program/session-schedule/json'):
            # ddu 2012
            schedule = [s['session'] for s in schedule['ddu2012']]
            # pprint( schedule )
            s_keys = list(schedule[0].keys())
            print(s_keys)
            v_keys=('id',
                'location','sequence',
                'name','slug', 'authors','emails', 'description',
                'start','duration',
                'released', 'license', 'tags',
                'conf_key', 'conf_url',
                'host_url', 'public_url',
                )
            print([k for k in v_keys if k in s_keys])
            print([k for k in v_keys if k not in s_keys])

            return self.ddu(schedule,show)

    def add_more_options(self, parser):
        parser.add_option('--schedule',
          help='URI of schedule data - gets stored in new show record' )
        parser.add_option('-u', '--update', action="store_true",
          help='update when diff, else print' )
        parser.add_option('-k', '--keys', action="store_true",
          help='dump keys of input stream' )
        parser.add_option('--reslug', action="store_true",
          help='regenerate slugs' )

    def work(self):
      print("working")
      if self.options.client and self.options.show:

        client,created = Client.objects.get_or_create(slug=self.options.client)
        if created:
          client.name = self.options.client.capitalize()
          client.save()

        show,created = Show.objects.get_or_create(
                             client=client,slug=self.options.show)
        if created:
          show.name = self.options.show.capitalize()
          show.schedule_url = self.options.schedule
          show.save()

        if self.options.whack:
            # DRAGONS!
            # clear out previous runs for this show

            rfs = Raw_File.objects.filter(show=show)
            if rfs and not self.options.force:
                print("There are Raw Fiels... --force to whack.")
                print(rfs)
                print("whacking aborted.")
                return False

            rfs.delete()
            Episode.objects.filter(show=show).delete()

        self.show = show
        self.one_show(show)

if __name__ == '__main__':
    p=add_eps()
    p.main()

