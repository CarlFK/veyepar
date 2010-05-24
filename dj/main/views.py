from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from django.core.paginator import Paginator, InvalidPage
from django.conf import settings

from django import forms
from django.forms import ModelForm
from django.forms.formsets import formset_factory

from django.db.models import Q

from django.http import HttpResponse, HttpResponseRedirect
from django.core import serializers
from django.core.urlresolvers import reverse

from django.utils import simplejson

import datetime
# from datetime import timedelta
import os
import csv
from cStringIO import StringIO

# from dabo.dReportWriter import dReportWriter

from main.models import Client,Show,Location,Episode,Cut_List
from main.forms import Episode_Form_small, Episode_Form_Preshow, clrfForm

from accounts.forms import LoginForm

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

    print ret

    response = HttpResponse(simplejson.dumps(ret,indent=1))
    response['Content-Type'] = 'application/json'

    return response

def ajax_user_lookup_form(request):
    return render_to_response('test.html',
        context_instance=RequestContext(request) )

def eps_xfer(request,client_slug=None,show_slug=None):
    """
    Returns all the episodes for a show as json.
    Used to synk blip url's with the main conference site.
    """

    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    eps = Episode.objects.filter(show=show)

    fields=('id','location','sequence','primary','target',
        'name','authors','description','start','duration')

    # response = HttpResponse(mimetype="text/javascript")
    response = HttpResponse(mimetype="application/json")
    # response['Content-Disposition'] = \
    #    'attachment; filename=%s.json' % show_slug
    serializers.serialize("json", eps, fields=fields,  stream=response)

    return response

def main(request):
    return render_to_response('main.html',
        context_instance=RequestContext(request) )

def meet_ann(request,show_id):
    show=get_object_or_404(Show,id=show_id)
    client=show.client
    episodes=Episode.objects.filter(show=show).order_by('sequence')
    location=episodes[0].location
    return render_to_response('meeting_announcement.html',
        {'client':client,'show':show,
          'location':location,
          'episodes':episodes,
        },
        context_instance=RequestContext(request) )

def recording_sheets(request,show_id):
    show=get_object_or_404(Show,id=show_id)
    episodes=Episode.objects.filter(show=show,start__day=21).order_by('location','start')

    base  = os.path.dirname(__file__)
    print base
    rfxmlfile  = os.path.join(base,'templates','RecordingSheet_v2a.rfxml')
    # fontfile = get_templete_abspath('badges/fonts/FreeSans.ttf')
     
    # buffer to create pdf in
    buffer = StringIO()

    # nonstandard font.  (not sure what standard is.)
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
          'episode_primary':ep.primary,
          'episode_start':ep.start,
          'episode_duration':ep.duration,
          'episode_end':ep.end,
          'location_name':location_name,
          'show_name':show.name })
        
    # generate the pdf in the buffer, using the layout and data
    print ds
    rw = dReportWriter(OutputFile=buffer, ReportFormFile=rfxmlfile, Cursor=ds)
    rw.write()

    # get the pdf out of the buffer
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(mimetype='application/pdf')
    response['Content-Disposition'] = 'filename=recording_sheets.pdf'
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
        pathname = os.path.join(settings.MEDIA_ROOT,client.slug,show.slug,'dv',cut.raw_file.location.slug, cut.raw_file.filename )
        writer.writerow([pathname])

    return response

def enc_play_list(request,episode_id):
    episode=get_object_or_404(Episode,id=episode_id)

    response = HttpResponse(mimetype='audio/mpegurl')
    response['Content-Disposition'] = 'attachment; filename=playlist.m3u'

    writer = csv.writer(response)
    for ext in [ 'ogv','flv', 'mp4', 'm4v', 'ogg', 'mp3' ]:
        pathname = os.path.join( settings.MEDIA_ROOT,client.slug,show.slug,ext,
            '%s.%s' % (episode.slug, ext) )
        writer.writerow([pathname])

    return response


def play_list(request,show_id):
    show=get_object_or_404(Show,id=show_id)
    episodes=Episode.objects.filter(show=show,state=3).order_by('sequence')

    response = HttpResponse(mimetype='audio/mpegurl')
    response['Content-Disposition'] = 'attachment; filename=playlist.m3u'

    writer = csv.writer(response)
    for ep in episodes:
        ext='flv'
        pathname = os.path.join( settings.MEDIA_ROOT,client.slug,show.slug,ext,
            '%s.%s' % (ep.slug, ext) )
        writer.writerow([pathname])

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
                print form.errors
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
    client_form, clients = former(
        request, Client, {},{'sequence':1})

    return render_to_response('clients.html',
        {'clients':clients,
        'client_form':client_form},
       context_instance=RequestContext(request) )

def client(request,client_slug=None):
    # the selected client and
    # list of client's shows and a blank to enter a new show

    client=get_object_or_404(Client,slug=client_slug)

    show_form, shows = former(
        request, Show, {'client':client.id}, {'sequence':1})

    return render_to_response('client.html',
        {'client':client,
        'show_form':show_form,
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
 
def episodes(request, client_slug=None, show_slug=None):
    # the selected client and show
    # and blanks to enter a new location and episode.
    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    locations=show.locations.all()
    episodes=Episode.objects.filter(show=show).order_by('sequence')

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
                    'duration':episode.duration}
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
            }
        form=Episode_Form_Preshow(initial=inits)
    else:
        # set this so 'episode_form':form doesn't blow up
        # there are other ways of doing this, they suck too.
        form = None

    return render_to_response('show.html',
        {'client':client,'show':show,
          'locations':locations,
          'episodes':episodes,
          'episode_form':form,
        },
        context_instance=RequestContext(request) )

 

def overlaping_episodes(request,show_id):

    show=get_object_or_404(Show,id=show_id)
    client=show.client
    episodes=Episode.objects.raw('select e1.* from main_episode e1, main_episode e2 where e1.id != e2.id and e1.start<e2.end and e1.end>e2.start and e1.location_id=e2.location_id order by e1.location_id, e1.start')
    elist=list(episodes)
    elist=[e.__dict__ for e in episodes]
    start,end=24*60,0
    for e in elist:
        e['start_min']=e['start'].hour*60+e['start'].minute
        e['end_min']=e['end'].hour*60+e['end'].minute
        if e['start_min'] < start: start = e['start_min']
        if e['end_min'] > end: end = e['start_min']
    width_min = end-start

    width_px=300.0
    x=width_min/width_px ## this here to do float math
    for e in elist:
        e['start_px']=int((e['start_min']-start)/x)
        e['end_px']=int((e['end_min']-start)/x)
        e['width_px']=(e['end_px']-e['start_px'])

    return render_to_response('overlaping_episodes.html',
        {
          'episodes':elist,
	},
        context_instance=RequestContext(request) )



def episode(request, episode_no):

    episode=get_object_or_404(Episode,id=episode_no)
    show=episode.show
    location=episode.location
    client=show.client


    try:
        prev_episode = episode.get_previous_by_start(state=episode.state)
    except Episode.DoesNotExist:
        # at edge of the set of nulls or values.  
        # In this app, *nulls come before values*.
        if episode.start is not None:
            # we are at the first value, try to go to the last null
            try:
                prev_episode = Episode.objects.filter(start__isnull=True).order_by('id').reverse()[0]
            except Episode.DoesNotExist:
                # There are no nulls
                prev_episode = None
        else:
            # there is no privious null, we have nowhere to go.
            prev_episode = None
           
    try:
        next_episode = episode.get_next_by_start(state=episode.state)
    except Episode.DoesNotExist:
        # at edge of the set of nulls or values.  
        # In this app, *values come after nulls*.
        if episode.start is None:
            # we are at the *last null*, so go to the *first value*
            try:
                next_episode = Episode.objects.filter(start__isnull=False).order_by('id')[0]
            except Episode.DoesNotExist:
                # There are no values
                next_episode = None
        else:
            # there is no *next value*, we have nowhere to go.
            next_episode = None
            
    cuts = Cut_List.objects.filter(episode=episode).order_by('sequence','raw_file__start','start')

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
            print "ep errors:", episode_form.errors
            print clrfformset.errors
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
        'MEDIA_ROOT':settings.MEDIA_ROOT,
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
