from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.template import Context, loader

from django.core.paginator import Paginator, InvalidPage
from django.conf import settings

from django import forms
from django.forms import ModelForm
from django.forms.formsets import formset_factory

from django.db.models import Q

from django.http import HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.core.urlresolvers import reverse
from django.core.mail import get_connection, EmailMessage

from django.utils import simplejson

import datetime
# from datetime import timedelta
import os
import csv
from copy import deepcopy

from cStringIO import StringIO
from pprint import pprint
import operator

from dabo.dReportWriter import dReportWriter

from main.models import Client,Show,Location,Episode,Cut_List,Raw_File
from main.models import fnify
from main.models import STATES, ANN_STATES
from main.forms import Episode_Form_small, Episode_Form_Preshow, clrfForm

from accounts.forms import LoginForm



def make_test_data():
    desc = """
Sample files and episode:  
file 0 and 4 are outside the range
file 1 and 3 are overlap the episode start/end
file 2 inside the start/end
e=episode,r=raw files
time: 0  1  2  3  4  5  6  7
raws:  00 11111 22 33333 44
episode:     XXXXXXXXX
"""

    # get/create a location, client and show.
    # append additional episodes 

    loc,create = Location.objects.get_or_create(name='test loc',slug='test_loc')
    client,create = Client.objects.get_or_create(name='test client',slug='test_client', host_user='veyepar_test', title_svg='test_pattern_1.svg', credits="00000001.png")

    show,create = Show.objects.get_or_create(name='test show',slug='test_show',client=client)
    if create:
        show.locations.add(loc)

    # datetime matches what run_tests.sh uses to create files.
    # the scheduled start time is at 4 seconds
    # in the middle of the 2nd clip
    t=datetime.datetime(2010,5,21,0,0,4)

    ep = Episode.objects.create(
        show=show,
        location=loc,
        state=1,
        released=True,
        start = t,
        duration = "00:00:06",
        )

    ep.name = "Test Episode" 
    ep.sequence = 1
    ep.description = desc
    ep.authors = 'test author'
    ep.save()

    return ep

def del_test_data():
    clients = Client.objects.filter(slug='test_client')
    if clients: clients[0].delete()

def tests(request):

    if request.method == 'POST': 
        if request.POST.has_key('create'):
            make_test_data()
        if request.POST.has_key('delete'):
            del_test_data()

    locations=Location.objects.filter(slug__contains="test")
    clients=Client.objects.filter(slug__contains="test")
    shows=Show.objects.filter(slug__contains="test")
    episodes=Episode.objects.filter(slug__contains="test")

    return render_to_response('tests.html',
       locals(),
       context_instance=RequestContext(request) )

def ajax_user_lookup(request):
    """
    looks up a username.
    returns an error code, username and human name
    """

    username = request.POST.get('username', False)
    users = User.objects.filter(username=username)

    ret = {}
    if users:
        user=users[0]
        # existing username
        ret['error_no']=0
        ret['id']=user.id
        ret['username']=user.username
        # if the first/last is blank, use username
        fn = user.get_full_name()
        ret['fullname'] = fn if fn else user.username
    else:
        # not found
        ret['error_no']=3
        ret['error_text']="not found."

    response = HttpResponse(simplejson.dumps(ret,indent=1))
    response['Content-Type'] = 'application/json'

    return response

def ajax_user_lookup_form(request):
    return render_to_response('test.html',
        context_instance=RequestContext(request) )

def eps_xfer(request,client_slug=None,show_slug=None):
    """
    Returns all the episodes for a show as json.
    Used to synk public url's with the main conference site.
    """

    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    eps = Episode.objects.filter(show=show)

    fields=('id','location','sequence',
            'conf_key', 'conf_url',
            'host_url', 'publiv_url',
        'name','slug', 'authors','emails', 'description',
        'start','duration', 
        'released', 'license', 'tags')

    response = HttpResponse(mimetype="application/json")
    serializers.serialize("json", eps, fields=fields,  stream=response)

    return response

def main(request):
    return render_to_response('main.html',
        context_instance=RequestContext(request) )

def meet_ann(request,show_id):
    show=get_object_or_404(Show,id=show_id)
    client=show.client
    episodes=Episode.objects.filter(show=show).order_by('start')
    location=episodes[0].location
    t = loader.get_template('meeting_announcement.html')
    c = Context(
        {'client':client,'show':show,
          'ANN_STATES': ANN_STATES,
          'location':location,
          'episodes':episodes,
    })
    r = t.render(c)
    if request:
        return HttpResponse(r)
    else:
        # called from emailer
        r=r.split('\n')
        subject = r[1]
        body = '\n'.join(r[3:])
        return subject,body

def emailer(show_id, ):
    show=get_object_or_404(Show,id=show_id)

    # show.announcement_state drives which of the following 3 get used:
    # 1 preview is for proofing the whole thing
    # 2. review is for the presenters to review their part
    # 3. approved means it is ready for distribution

    admin_emails = ['carl@personnelware.com', ]

    def author_emails(show):
        # return a list of email addresses for the show
        pems = [ 'brianhray@gmail.com']
        episodes=Episode.objects.filter(show=show)
        for ep in episodes:
            if ep.emails:
                pems.append(ep.emails)
        return pems

    announce_lists = [
 '"ChiPy" <chicago@python.org>', '"ChiPy Announce" <ChiPy-announce@python.org>',
 '"PS1" <pumping-station-one-public@googlegroups.com>',
 '"ACM Chicago" <mtemkin@speakeasy.net>',
 '"ACM Chicago" <chicago-chapter-acm@googlegroups.com>',
 #'"Linux Users Of Northern Illinois" <luni@luni.org>', 
 '"LUNI-Announce" <luni-announce@luni.org>', 
 '"Chicago Linux Discuss" <chicagolinux-discuss@googlegroups.com>',
 '"UFO Chicago" <ufo@ufo.chicago.il.us>', 
 # '<genluglist@codlug.info>',
 #'<chicagotechcal@gmail.com>',
 'clclinuxclub@gmail.com',
 ]
#     tos = { 1: admin_emails,
#             2: author_emails(show),
#             3: announce_lists}[show.announcement_state]

    if show.announcement_state == 1:
        tos = admin_emails
    else:
        tos = author_emails(show)

    subject,body=meet_ann(None,show_id)
    print subject
    print body
    print tos
    
    # connect to the smtp server
    connection = get_connection()
    sender = 'Carl Karsten <cfkarsten@gmail.com>'
    headers = {
        # 'Reply-To': "ChiPy <chicago@python.org>"
        # 'From': sender,
        }
    for to in tos:
        email = EmailMessage(subject, body, sender, [to], headers=headers ) 
        ret = connection.send_messages([email])
        print to, ret

    return

def schedule(request, show_id, show_slug):
    show=get_object_or_404(Show,id=show_id)
    locations=show.locations.all().order_by('sequence')
    episodes=Episode.objects.filter(show=show)

    # order_by to override Meta: ordering = ["sequence"]
    # which will get included in the field list and break the .distinct().
    times=episodes.order_by('start').values('start','end').distinct()
    times=episodes.order_by('start').values('start').distinct()
    # starts=[ s['start'] for s in starts]

    dates = list(set(t['start'].date() for t in times))
    dates.sort()

    # pprint([s for s in starts if s.date()==dates[1]])
        
    # [[d1,[[t1,[e1,e2,e3]],
    #       [t2,[e4,e5,e6]]],
    #  [d2,[[t3,[e7,e8,e9]]]]]]
    days=[]
    for d in dates:
        rows=[]
        for t in times:
            if t['start'].date() == d:
                slots=[]
                for loc in locations: 
                    i=None
                    for ep in episodes:
                        if ep.location == loc and  ep.start == t['start'] : 
                            # ep.start == t['start'] and  ep.end == t['end']: 
                            i = ep
                    slots.append(i)
                rows.append([t,slots])
        days.append([d,rows])

    # pprint(days)

    return render_to_response('schedule.html',
        {'show':show, 
        'locations':locations,
        'days':days},
        context_instance=RequestContext(request) )
    
def room_signs(request,show_id):
    show=get_object_or_404(Show,id=show_id)
    episodes=Episode.objects.filter(show=show).order_by('location','start')

    base  = os.path.dirname(__file__)
    rfxmlfile  = os.path.join(base,'templates','TalkSigns.rfxml')
     
    # buffer to create pdf in
    buffer = StringIO()

    # nonstandard font.  (not sure what standard is.)
    # fontfile = get_templete_abspath('badges/fonts/FreeSans.ttf')
    # pdfmetrics.registerFont(TTFont("FreeSans", fontfile))
    
    ds=[]
    for ep in episodes:
        if ep.location:
            location_name=ep.location.name
        else:
            location_name='None'
        ds.append({'episode_id':ep.id,
          'episode_name':ep.name,
          'episode_authors':ep.authors,
          'episode_primary':ep.conf_key,
          'episode_start':ep.start,
          'episode_duration':ep.duration,
          'episode_end':ep.end,
          'episode_released':ep.released,
          'location_name':location_name,
          'show_name':show.name })
        
    # generate the pdf in the buffer, using the layout and data
    rw = dReportWriter(OutputFile=buffer, ReportFormFile=rfxmlfile, Cursor=ds)
    rw.write()

    # get the pdf out of the buffer
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = \
      'filename=%s_room_signs.pdf' % ( show.slug )
    response.write(pdf)
    return response


    
def recording_sheets(request,show_id):
    show=get_object_or_404(Show,id=show_id)
    client = show.client

    # kwargs = {'location': location_slug, 'start__day':start_day, 'state':state}
    episodes=Episode.objects.filter(show=show).order_by('location','start')

    base  = os.path.dirname(__file__)
    rfxmlfile  = os.path.join(base,'templates','RecordingSheet_v2a.rfxml')
     
    # buffer to create pdf in
    buffer = StringIO()

    # nonstandard font.  (not sure what standard is.)
    # fontfile = get_templete_abspath('badges/fonts/FreeSans.ttf')
    # pdfmetrics.registerFont(TTFont("FreeSans", fontfile))
    
    ds=[]
    for ep in episodes:
        if ep.location:
            location_name=ep.location.name
        else:
            location_name='None'
        ds.append({'episode_id':ep.id,
          'episode_name':ep.name,
          'episode_authors':ep.authors,
          'episode_primary':ep.conf_key,
          'episode_start':ep.start,
          'episode_duration':ep.duration,
          'episode_end':ep.end,
          'episode_released':ep.released,
          'location_name':location_name,
          'client_name':client.name,
          'show_name':show.name,
          })
        
    # generate the pdf in the buffer, using the layout and data
    rw = dReportWriter(OutputFile=buffer, ReportFormFile=rfxmlfile, Cursor=ds)
    rw.write()

    # get the pdf out of the buffer
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = \
      'filename=%s_recording_sheets.pdf' % ( show.slug )
    response.write(pdf)
    return response

def raw_play_list(request,episode_id):
    episode=get_object_or_404(Episode,id=episode_id)
    show=episode.show
    client=show.client
    cuts = Cut_List.objects.filter(
                episode=episode,apply=True).order_by('raw_file__start')

    response = HttpResponse(mimetype='audio/mpegurl')
    response['Content-Disposition'] = 'attachment; filename=playlist.m3u'

    writer = csv.writer(response)
    for cut in cuts:
	head=settings.MEDIA_URL
	# head="/home/juser/Videos/veyepar"
        pathname = os.path.join(head,client.slug,show.slug,'dv',cut.raw_file.location.slug, cut.raw_file.filename )
        writer.writerow([pathname])

    return response

def enc_play_list(request,episode_id):
    episode=get_object_or_404(Episode,id=episode_id)
    show =episode.show
    client=show.client

    response = HttpResponse(mimetype='audio/mpegurl')
    response['Content-Disposition'] = 'attachment; filename=playlist.m3u'

    writer = csv.writer(response)
    # exts = [ 'ogv','flv', 'mp4', 'm4v', 'ogg', 'mp3' ]:
    exts = [ 'mp4', ]
    for ext in exts:
        
      foot_pathname = os.path.join(client.slug,show.slug, ext, '%s.%s' % (episode.slug, ext))
      print os.path.join(os.path.expanduser('~/Videos/veyepar'), foot_pathname)

      if os.path.exists( 
          os.path.join(os.path.expanduser('~/Videos/veyepar'), foot_pathname)):
        
        if settings.MEDIA_URL.startswith('file:/'):
            head=settings.MEDIA_URL
        else:
            # probably no local file access
            # head='http://'+request.META['HTTP_HOST']+settings.MEDIA_URL
            head=settings.MEDIA_URL
            # so review the smaller iPhone file
        item = '/'.join([head, foot_pathname ] )
        writer.writerow([item])


    return response


def play_list(request,show_id,location_slug=None):
    show=get_object_or_404(Show,id=show_id)
    client=show.client
    episodes=Episode.objects.filter(show=show,state=3).order_by('sequence')
    if location_slug:
        episodes = episodes.filter(location__slug=location_slug)

    response = HttpResponse(mimetype='audio/mpegurl')
    response['Content-Disposition'] = 'attachment; filename=playlist.m3u'

    writer = csv.writer(response)
    for ep in episodes:
        # pathname = os.path.join( settings.MEDIA_URL,client.slug,show.slug,ext,
        if settings.MEDIA_URL.startswith('file:/'):
            head=settings.MEDIA_URL
            ext='flv'
        else:
            # probably no local file access
            head='http://'+request.META['HTTP_HOST']+settings.MEDIA_URL
            # so review the smaller iPhone file
            ext='m4v'
        item = '/'.join([head, client.slug,show.slug,ext, '%s.%s' % (ep.slug, ext)] )
        writer.writerow([item])

    return response

def meet_ical(request,location_id):
    location=get_object_or_404(Location,id=location_id)
    show=location.show
    client=show.client
    episodes=Episode.objects.filter(show=show).order_by('sequence')
    location=episodes[0].location
    return render_to_response('meeting_announcement.html',
        {'client':client,'show':show,
          'location':location,
          'episodes':episodes,
        },
        context_instance=RequestContext(request) )

def former(request, Model, parents, inits={}):

    class xForm(ModelForm):
        class Meta:
            model=Model

    if True or request.user.is_authenticated():
        if request.method == 'POST':
            form=xForm(request.POST)
            if form.is_valid():
                form.save()
            else:
                # print form.errors
                pass
        else:
            # add parents to inits
            inits.update(parents)
            form=xForm(initial=inits)
    else:
        form=None

    objects=Model.objects.filter(**parents).order_by('sequence')
    return form,objects

def clients(request):
    # list of clients and a blank to enter a new one

    class Client_Form(ModelForm):
        class Meta:
            model=Client
            fields=('name','slug','tags','description')


    if request.user.is_authenticated():
        if request.method == 'POST':
            # client=Client(sequence=1)
            # form=Client_Form(request.POST,instance=client)
            form=Client_Form(request.POST)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse(client, args=(form.cleaned_data['slug'],)))
            else:
                pass
                # print form.errors
        else:
            form=Client_Form(initial={'sequence':1})
    else:
        form=None

    clients=Client.objects.all().order_by('sequence')

    return render_to_response('clients.html',
        {'clients':clients,
        'client_form':form},
       context_instance=RequestContext(request) )


def client(request,client_slug=None):
    # the selected client and
    # list of client's shows and a blank to enter a new show

    client=get_object_or_404(Client,slug=client_slug)

    class Show_Form(ModelForm):
        class Meta:
            model=Show
            fields=('name','slug','locations','tags','description')

    if request.user.is_authenticated():
        if request.method == 'POST':
            show=Show(client=client,sequence=1,)
            form=Show_Form(request.POST,instance=show)
            if form.is_valid():
                form.save()
                return HttpResponseRedirect(reverse(episodes, args=(client_slug, form.cleaned_data['slug'])))
            else:
                pass
                # print form.errors
        else:
            locations=Location.objects.filter(active=True).order_by('sequence')
            form=Show_Form(
                initial={'client':client.id, 'sequence':1,
                         'locations': [o.pk for o in locations] })
    else:
        form=None

    shows=Show.objects.filter(client=client).order_by('sequence')

    return render_to_response('client.html',
        {'client':client,
        'show_form':form,
        'shows':shows},
       context_instance=RequestContext(request) )

def locations(request):
    location_form, locations = former(
        request, Location, {},{'sequence':1})
    return render_to_response('locations.html',
        {
          'locations':locations,
          'location_form':location_form,
        },
	context_instance=RequestContext(request) )
 
def show_stats(request, show_id, ):
    """
    Show Status - varous summaries of rooms, days and the whole thing
    """

    show=get_object_or_404(Show,id=show_id)
    client=show.client
    episodes=Episode.objects.filter(show=show,location__active=True)
    locked=Episode.objects.filter(show=show, locked__isnull=False).order_by('locked')
    raw_files=Raw_File.objects.filter(show=show)
    locations=show.locations.filter(active=True).order_by('sequence')
    
    empty_stat = {'count':0,'minutes':0, 
               'start':None, 'end':None, 'states':[0]*len(STATES),
               'files':0, 'bytes':0, 
               'loc':None, 'date':None }
 
    dates=[] 
    for ep in episodes:
        dt = ep.start.date()
        if dt not in dates: dates.append(dt)
    dates.sort()
    
    # show totals:
    show_stat = deepcopy(empty_stat)

    # make 3 dicts of empty stats
    # 1. for each room-day (date,loc)
    stats={} 
    for loc in locations: 
        for dt in dates: 
            d = deepcopy(empty_stat)
            d['loc'] = loc
            d['date'] = dt
            stats[(dt,loc.id)] = d

    # 2. for locations:
    d={}
    for loc in locations:
        d[loc.id] = deepcopy(empty_stat)
        d[loc.id]['loc'] = loc
    locations=d

    # 3. for dates:
    d={}
    for dt in dates:
        d[dt] = deepcopy(empty_stat)
    dates=d

    # gather episode stats
    # func to update one:
    def add_ep_to_stat(ep,stat):
        stat['count']+=1        
        duration=ep.end-ep.start        
        stat['minutes']+=duration.seconds/60        
        stat['start']=ep.start if stat['start'] is None else min(stat['start'],ep.start)
        stat['end']=ep.end if stat['end'] is None else max(stat['end'],ep.end)
        if 0<= ep.state <= len(STATES):
            stat['states'][ep.state]+=1        
        else:
            stat['states'][0]+=1        

    for ep in episodes:
        dt = ep.start.date()
        loc = ep.location.id

        # update grand total:
        add_ep_to_stat(ep,show_stat)
        
        # update total for date:
        add_ep_to_stat(ep,dates[dt])
        
        # update total for location:
        add_ep_to_stat(ep,locations[loc])
        
        # update room-loc
        add_ep_to_stat(ep,stats[(dt,loc)])
        

    def add_rf_to_stat(rf,stat):
        stat['files'] += 1
        stat['bytes'] += rf.filesize

    # gather raw_file stats
    for rf in raw_files:
        dt = rf.start.date()
        loc = rf.location.id

        add_rf_to_stat(rf,show_stat)
        add_rf_to_stat(rf,dates[dt])
        add_rf_to_stat(rf,locations[loc])
        add_rf_to_stat(rf,stats[(dt, loc)])
        

    # make lists out of the dics cuz I can't figur out how to get at the dict
 
    # and do some more calcs
    def calc_stat(stat):
            stat['hours']=int( stat['minutes']/60.0 + .9)
     
            stat['talk_gig']=int(stat['minutes']*13/60)
            stat['gig']=stat['bytes']/(1024**3)
            stat['max_gig']=(stat['end']-stat['start']).seconds*13/3600

            if stat['talk_gig'] < stat['gig'] < stat['max_gig']:
                # amount recoreded between all talks and below cruft
                stat['variance'] = 0
            else:
                if stat['gig'] < stat['talk_gig']:
                    # amount recoreded less than expected
                    stat['variance'] = stat['gig'] - stat['talk_gig']	
                else:
                    # amount recoreded over talks+cruft
                    stat['variance'] = stat['talk_gig'] - stat['gig']	

            # alarm is % of expected gig, 0=perfect, 20 or more = wtf?
            stat['alarm']= int( abs(stat['variance']) / (stat['minutes']/60.0*13 + 1) * 100 )
            stat['alarm_color'] = "%02x%02x%02x" % ( 255, 255-stat['alarm'], 255-stat['alarm'] )
            return stat
 
    show_stat = calc_stat(show_stat)
    l = []
    for dt in dates:
        d = dates[dt]
        d['date'] = dt
        d = calc_stat(d)
        l.append(d)
    l.sort(key=operator.itemgetter('date'))
    dates=l
    # pprint(dates)
 
    l = []
    for loc in locations:
        d = locations[loc]
        d['seq'] = d['loc'].sequence
        d = calc_stat(d)
        l.append(d)
    l.sort(key=operator.itemgetter('seq'))
    locations=l
    # pprint(locations)

    rows=[]
    for dt in dates: 
        dt=dt['date']
        row=[]
        for loc in locations: 
            stat = calc_stat(stats[(dt,loc['loc'].id)])
            row.append(stat)
        rows.append(row)
    
    states = zip( show_stat['states'], STATES)
    rows = zip(dates,rows)

    max_title_len = max( len(ep.name) for ep in episodes )
    max_authors_len = max( len(ep.authors) for ep in episodes )

    max_name_len = 0
    max_authors_len = 0
    for ep in episodes:
        if len(ep.name) > max_name_len:
            max_name_len = len(ep.name)
            max_name_ep = ep
        if len(ep.authors) > max_authors_len:
            max_authors_len = len(ep.authors)
            max_authors_ep = ep

    return render_to_response('show_stats.html',
        {
          'client':client,
          'show':show,
          'locations':locations,
          'show_stat':show_stat,
          'locations':locations,
          'rows':rows,
          'states':states,
          'locked':locked,
          'max_name_ep':max_name_ep,
          'max_authors_ep':max_authors_ep,
        },
	context_instance=RequestContext(request) )


def episodes(request, client_slug=None, show_slug=None, location_slug=None,
              start_day=None, state=None):
# def episodes(request, client_slug=None, show_slug=None):
    # the selected client, show and episodes
    # episode entry form
    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    # location_slug = request.REQUEST.get('location')
    # start_day = request.REQUEST.get('start_day')
    # state = request.REQUEST.get('state')
    # raise Exception((client_slug, show_slug, state, start_day, location_slug))
    locations=show.locations.filter(active=True).order_by('sequence')
    episodes=Episode.objects.filter(show=show).order_by('sequence')

    kwargs = {'location': location_slug, 'start__day':start_day, 'state':state}
    # raise Exception(episodes.filter(**kwargs))
    if location_slug:
        # location here is for default location for new episodes
        location=get_object_or_404(Location,slug=location_slug)
        episodes=episodes.filter(show=show,location=location)
    if start_day:
        episodes = episodes.filter(start__day=start_day)
    if state:
      episodes = episodes.filter(state=state)
      #   if state=='0':
      #  episodes = episodes.filter(state__isnull=True)

    
    # calc total time and dv size
    total_minutes=0
    for e in episodes:
        seconds = reduce(lambda x, i: x*60 + i,
            map(float, e.duration.split(':')))
        # add 5 min to each talk to accomdate talks going over 
        # and recording break time 
        minutes = seconds/60 
        total_minutes += minutes
    total_episodes = episodes.count()
    total_hours = total_minutes / 60
    total_gig = total_hours * 13
    fudge_hours = (total_minutes + 5 * total_episodes) / 60
    fudge_gig = fudge_hours *13

    if request.user.is_authenticated():
        if request.method == 'POST':
            form=Episode_Form_Preshow(request.POST)
            if form.is_valid():
                episode = form.save()
                # setup next form
                # use saved Episode as a base for defaults
                inits={
                    'show':show.id,
                    'location':episode.location.id,
                    'sequence':episode.sequence+1,
                    'start':episode.end,
                    'duration':episode.duration,
                    'state':1,
                    }
                # roll the new episode into the query set
                episodes=Episode.objects.filter(show=show).order_by('sequence')
            else:
                # print form
                inits=None # (prevents form from being created below)
        else:
            if episodes:
                # use last Episode as a base for defaults
                episode = episodes[len(episodes)-1]
                location = episode.location.id
                sequence = episode.sequence+1
                start = episode.end
            else:
                # firt Episode of the show
                location = locations[0].id
                sequence = 1
                # today at 6pm
                start = datetime.datetime.combine(
                            datetime.date.today(),datetime.time(18))
            inits = {
                'show':show.id,
                'location':location,
                'sequence':sequence, 
                'start': start,
                'duration':'00:45:00',
                'state':1,
            }
        if inits: 
            form=Episode_Form_Preshow(initial=inits, locations=locations)
    else:
        # set this so 'episode_form':form doesn't blow up
        # there are other ways of doing this, they suck too.
        form = None

    return render_to_response('show.html',
        {'client':client,'show':show,
          'locations':locations,
          'location_slug':location_slug,
          'episodes':episodes,
          'total_episodes':total_episodes,
          'episode_form':form,
          'total_hours': total_hours,
          'total_gig': total_gig,
          'fudge_hours': fudge_hours,
          'fudge_gig': fudge_gig,
        },
        context_instance=RequestContext(request) )

 

def overlaping_episodes(request,show_id):

    show=get_object_or_404(Show,id=show_id)
    client=show.client
    episodes=Episode.objects.raw('select distinct e1.* from main_episode e1, main_episode e2 where e1.id != e2.id and e1.start<e2.end and e1.end>e2.start and e1.location_id=e2.location_id and e1.show_id=%s and e2.show_id=%s order by e1.location_id, e1.start', [show.id,show.id])
    elist=[e.__dict__ for e in episodes]
    start,end=24*60,0
    for e in elist:
        e['location']=Location.objects.get(id=e['location_id'])
    start,end=24*60,0
    for e in elist:
        e['start_min']=e['start'].hour*60+e['start'].minute
        e['end_min']=e['end'].hour*60+e['end'].minute
        if e['start_min'] < start: start = e['start_min']
        if e['end_min'] > end: end = e['start_min']
    width_min = end-start

    width_px=300.0
    x=width_min/width_px +1 ## float math so that x isn't an int
    for e in elist:
        e['start_px']=int((e['start_min']-start)/x)
        e['end_px']=int((e['end_min']-start)/x)
        e['width_px']=(e['end_px']-e['start_px'])

    return render_to_response('overlaping_episodes.html',
        {
          'episodes':elist,
	},
        context_instance=RequestContext(request) )


def orphan_dv(request,show_id):
    """
    dv files that are not associated with an episode.
    """
    
    show=get_object_or_404(Show,id=show_id)
    # rfs=Raw_File.objects.filter(location=location,show=show).order_by('start')
    rfs_all=Raw_File.objects.filter(show=show).order_by('start')
    rfs=[]
    for rf in rfs_all:
        if rf.cut_list_set.count()==0:
          dv=rf
          eps = Episode.objects.filter(
            Q(start__lte=dv.end)|Q(start__isnull=True),
            Q(end__gte=dv.start)|Q(end__isnull=True),
            location=dv.location)

          rfs.append([rf,eps])
    
    return render_to_response('orphan_dv.html',
        {
          'rfs':rfs,
	},
        context_instance=RequestContext(request) )

def mk_cuts(episode, 
        short_clip_time = 0,
        start_slop=0, end_slop=0):

    """
    short_clip_time - threshold for the person kinda maybe starts talking and doesn't.  cut, cut, cut = small clips that need to be discarded.
    so include them in the time window, but default to not included.

    start/end slop - extra time added to the start/end of the schedule to accommodate talks not starting or ending on time. 

    """

    # Get the overlaping dv,
    # plus some fuzz: 5 min before and 10 after.
    dvs = Raw_File.objects.filter(
            end__gte=episode.start - datetime.timedelta(minutes=start_slop),
            start__lte=episode.end + datetime.timedelta(minutes=end_slop),
            location=episode.location).order_by('start')

    seq=0
    started=False ## magic to figure out when talk really started
    for dv in dvs:
        seq+=1
        if dv.get_minutes() > short_clip_time : 
            started = True
        cl,created = Cut_List.objects.get_or_create(
            episode=episode,
            raw_file=dv)
        if created:
            cl.sequence=seq
            # if the talk has started, 
            # and the segment is in the time slot
            cl.apply = started and (dv.start < episode.end)
            cl.save()

    cuts = Cut_List.objects.filter(episode=episode).order_by('sequence','raw_file__start')

    return cuts
            


def episode(request, episode_no):

    episode=get_object_or_404(Episode,id=episode_no)
    show=episode.show
    location=episode.location
    client=show.client

    try:
        # why Start/End can't be null:
        # http://code.djangoproject.com/ticket/13611
        prev_episode = episode.get_previous_by_start(show=show)
    except Episode.DoesNotExist:
        # at edge of the set of nulls or values.  
        prev_episode = None
           
    try:
        next_episode = episode.get_next_by_start(show=show)
    except Episode.DoesNotExist:
        next_episode = None

    cuts = Cut_List.objects.filter(episode=episode).order_by('sequence','raw_file__start','start')

    if not cuts:
        cuts = mk_cuts(episode)

    clrfFormSet = formset_factory(clrfForm, extra=0)
    if request.user.is_authenticated() and request.method == 'POST': 
        episode_form = Episode_Form_small(request.POST, instance=episode) 
        clrfformset = clrfFormSet(request.POST) 
        if episode_form.is_valid() and clrfformset.is_valid(): 
            # if the state got bumpped, move to the next episode
            if episode.state:
                bump_ep = episode.state+1 == episode_form.cleaned_data['state']
            else:
                bump_ep = None
            episode_form.save()
            for form in clrfformset.forms:
                cl=get_object_or_404(Cut_List,id=form.cleaned_data['clid'])

                cl.raw_file.trash=form.cleaned_data['trash']
                cl.raw_file.comment=form.cleaned_data['rf_comment']
                cl.raw_file.save()

                cl.sequence=form.cleaned_data['sequence']
                cl.start=form.cleaned_data['start']
                cl.end=form.cleaned_data['end']
                cl.apply=form.cleaned_data['apply']

                cl.comment=form.cleaned_data['cl_comment']
                cl.save()
                if form.cleaned_data['split']:
                    cl.id=None
                    cl.sequence+=1
                    cl.save(force_insert=True)

            # if trash got touched, 
            # need to requery to get things in the right order.  I think.
            if bump_ep:
               episode = nextepisode
               episode_form = Episode_Form_small(instance=episode) 
            cuts = Cut_List.objects.filter(
                episode=episode).order_by('raw_file__trash','raw_file__start')
            init = [{'clid':cut.id,
                'trash':cut.raw_file.trash,
                'sequence':cut.sequence,
                'start':cut.start, 'end':cut.end,
                'apply':cut.apply,
                'cl_comment':cut.comment, 'rf_comment':cut.raw_file.comment,
                 } for cut in cuts]
            clrfformset = clrfFormSet(initial=init)

        else:
            pass
            # print "ep errors:", episode_form.errors
            # print clrfformset.errors
    else:
        episode_form = Episode_Form_small(instance=episode) 
        # init data with things in the queryset that need editing
        # this part seems to work.
        init = [{'clid':cut.id,
                'trash':cut.raw_file.trash,
                'sequence':cut.sequence,
                'start':cut.start, 'end':cut.end,
                'apply':cut.apply,
                'cl_comment':cut.comment, 'rf_comment':cut.raw_file.comment,
        } for cut in cuts]
        clrfformset = clrfFormSet(initial=init)

# If all the dates are the same, don't bother displaying them
    if episode.start is None or episode.end is None:
      same_dates = False
    else:
      talkdate = episode.start.date()
      same_dates = talkdate==episode.end.date()
      if same_dates:
        for cut in cuts:
            same_dates = same_dates and \
               talkdate==cut.raw_file.start.date()==cut.raw_file.end.date()

    return render_to_response('episode.html',
        {'episode':episode,
        'client':client, 'show':show, 'location':location,
        'prev_episode':prev_episode,
        'next_episode':next_episode,
        'same_dates':same_dates,
        'episode_form':episode_form,
        'clrffs':zip(cuts,clrfformset.forms),
        'clrfformset':clrfformset,
        },
    	context_instance=RequestContext(request) )
    	
def episode_logs(request, episode_id):
    episode = get_object_or_404(Episode, id=episode_id)
    logs = episode.log_set.all()
    return render_to_response('episode_logs.html',
        {'episode':episode,
         'logs':logs,
        },
        context_instance=RequestContext(request) )


def claim_episode_lock(request, episode_no):
    assert request.user.is_authenticated()

    episode = get_object_or_404(Episode, id=episode_no)

    episode.locked = datetime.now()
    episode.locked_by = request.user.username
    episode.save()

    return HttpResponseRedirect(
        reverse(
            'episode_list',
            kwargs={
                'client_slug': episode.show.client.slug,
                'show_slug': episode.show.slug}))
