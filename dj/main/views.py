from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from django.core.paginator import Paginator, InvalidPage

from django import forms
from django.forms import ModelForm
from django.forms.formsets import formset_factory

from django.db.models import Q

from django.http import HttpResponse
from django.core import serializers

from datetime import datetime
from datetime import timedelta
import os

from main.models import Client,Show,Location,Episode,Cut_List
from main.forms import EpisodeForm

from accounts.forms import LoginForm

def eps_xfer(request,client_slug=None,show_slug=None):
    """
    Returns all the episodes for a show as json.
    Used to synk blip url's with the main conference site.
    """

    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    eps = Episode.objects.filter(location__show=show)

    fields=('id','location','sequence','primary',
        'name','authors','description','start','end')

    response = HttpResponse(mimetype="text/javascript")
    response['Content-Disposition'] = \
        'attachment; filename=%s.json' % show_slug
    serializers.serialize("json", eps, fields=fields,  stream=response)

    return response

def main(request):
    return render_to_response('main.html',
        context_instance=RequestContext(request) )

def meet_ann(request,location_id):
    location=get_object_or_404(Location,id=location_id)
    show=location.show
    client=show.client
    episodes=Episode.objects.filter(location__show=show).order_by('sequence')
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
            form=xForm(inits)
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

def locations(request, client_slug=None, show_slug=None):
    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    location_form, locations = former(
        request, Location, {'show':show.id},{'sequence':1})
    return render_to_response('locations.html',
        {'client':client,'show':show,
          'locations':locations,
          'location_form':location_form,
        },
	context_instance=RequestContext(request) )
 
def episodes(request,
        client_slug=None,show_slug=None,location_slug=None):
    # the selected client and show
    # list of loctions (rooms) and episodes (talks)
    # and blanks to enter a new location and episode.
    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)

# show Episodes from all or one location
# seed the 'new Episode' form with the location.
    if location_slug:
        locations=Location.objects.filter(show=show, slug=location_slug)
        location=Location.objects.get(show=show, slug=location_slug)
        parents={'location':location.id}
    else:
        locations=Location.objects.filter(show=show)
        location=locations[0]
        parents={'location__show':show.id}

    form, episodes = None,None
    if locations:
        if request.user.is_authenticated():
            if request.method == 'POST':
                form=EpisodeForm(request.POST)
                if form.is_valid():
                    form.save()
# setup next time block to come after current one 
                    saved=form.cleaned_data
                    inits={
                        'location':location.id,
                        'sequence':saved["sequence"]+1,
                        'start':saved["end"],
                        'end':saved["end"]+(saved["end"]-saved["start"])}
                    inits.update(parents)
                    print inits
                    form=EpisodeForm(inits)
                else:
                    print form.errors
            else:
                inits = {'sequence':1, 'location':location.id}
                # add parents to inits
                inits.update(parents)
                # form=EpisodeForm(inits)
                inits={'start': datetime(2009, 12, 3, 19, 12), 'end': datetime(2009, 12, 3, 19, 36), 'location': 19, 'sequence': 4}
                form=EpisodeForm(inits)

            episodes=Episode.objects.filter(**parents).order_by('sequence')


    return render_to_response('show.html',
        {'client':client,'show':show,
          'locations':locations,
          'episodes':episodes,
          'episode_form':form,
        },
	context_instance=RequestContext(request) )
 
class Episode_Form(forms.Form):
    state = forms.IntegerField(label="State",
        widget=forms.TextInput(attrs={'size':':3'}))

class clrfForm(forms.Form):
    clid = forms.IntegerField(widget=forms.HiddenInput())
    trash = forms.BooleanField(label="Trash",required=False)
    apply = forms.BooleanField(label="Apply",required=False)
    split = forms.BooleanField(label="Spilt",required=False)
    sequence = forms.IntegerField(label="Sequence",required=False,
      widget=forms.TextInput(attrs={'size':'3'}))
    start = forms.CharField(max_length=12,label="Start",required=False,
      help_text = "offset from start in h:m:s or frames, blank for start",
      widget=forms.TextInput(attrs={'size':'9'}))
    end = forms.CharField(max_length=12,label="End",required=False,
      help_text = "offset from start in h:m:s or frames, blank for end",
      widget=forms.TextInput(attrs={'size':'9'}))
    rf_comment = forms.CharField(label="Raw_File comment",required=False,
      widget=forms.Textarea(attrs={'rows':'2','cols':'20'}))
    cl_comment = forms.CharField(label="Cut_List comment",required=False,
      widget=forms.Textarea(attrs={'rows':'2','cols':'20'}))

def episode(request,episode_no):

    episode=get_object_or_404(Episode,id=episode_no)
    location=episode.location
    show=location.show
    client=show.client

    episodes=Episode.objects.filter(id__gt=episode_no,location__show=episode.location.show).order_by('id')
    if episodes: nextepisode=episodes[0]
    else: nextepisode=episode

    # cuts = Cut_List.objects.filter(episode=episode).order_by('raw_file__trash','sequence','raw_file__start')
    cuts = Cut_List.objects.filter(episode=episode).order_by('sequence','raw_file__start')

    clrfFormSet = formset_factory(clrfForm, extra=0)
    if request.user.is_authenticated() and request.method == 'POST': 
        episode_form = Episode_Form(request.POST) 
        clrfformset = clrfFormSet(request.POST) 
        if episode_form.is_valid() and clrfformset.is_valid(): 
            episode.state=episode_form.cleaned_data['state']
            # print episode.state
            episode.save()
            for form in clrfformset.forms:
                cl=get_object_or_404(Cut_List,id=form.cleaned_data['clid'])

                cl.raw_file.trash=form.cleaned_data['trash']
                cl.raw_file.comment=form.cleaned_data['rf_comment']
                cl.raw_file.save()

                cl.sequence=form.cleaned_data['sequence']
                cl.start=form.cleaned_data['start']
                cl.end=form.cleaned_data['end']
                cl.apply=form.cleaned_data['apply']
                # print cl.apply, form.cleaned_data['apply']

                cl.comment=form.cleaned_data['cl_comment']
                cl.save()
                if form.cleaned_data['split']:
                    cl.id=None
                    cl.sequence+=1
                    cl.start = cl.end
                    cl.end = ''
                    cl.save(force_insert=True)

            # if trash got touched, 
            # need to requery to get things in the right order.  I think.
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
        episode_form = Episode_Form({'state':episode.state}) 
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
            # cut.raw_file.dur=cut.raw_file.durationhms()
            same_dates = same_dates and \
               talkdate==cut.raw_file.start.date()==cut.raw_file.end.date()

    return render_to_response('episode.html',
        {'episode':episode,
        'client':client, 'show':show, 'location':location,
        'nextepisode':nextepisode,
        'same_dates':same_dates,
        'episode_form':episode_form,
        'clrffs':zip(cuts,clrfformset.forms),
        'clrfformset':clrfformset,
        },
    	context_instance=RequestContext(request) )
    	
