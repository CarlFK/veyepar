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

from datetime import datetime
from datetime import timedelta
import os

from main.models import Client,Show,Location,Episode,Cut_List

def main(request):
    return render_to_response('main.html',
        context_instance=RequestContext(request) )

def client(request,client_slug=None):
    print client_slug
    client=get_object_or_404(Client,slug=client_slug)
    shows=Show.objects.filter(client=client)
    return render_to_response('client.html',
        {'client':client,'shows':shows},
       context_instance=RequestContext(request) )

def get_dv_files(path):
    # files=get_dv_files('/home/juser/temp/clojure/2009-may-meeting/sullys/dv')
    file_names=os.listdir(path)
    files=[{'name':n} for n in file_names]
    files=[]
    for file_name in os.listdir(path):
        d={'name':file_name,
           'size':os.path.getsize("%s/%s"%(path,file_name))
          }
        files.append(d)
    return files

def client_shows(request,client_slug=None,show_slug=None):
    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    locations=Location.objects.filter(show=show)
    episodes=Episode.objects.filter(location__show=show)
    return render_to_response('show.html',
        {'client':client,'show':show,
          'locations':locations,'episodes':episodes,
        },
	context_instance=RequestContext(request) )
 
class clrfForm(forms.Form):
    clid = forms.IntegerField(widget=forms.HiddenInput())
    delete = forms.BooleanField(label="Delete",required=False)
    trash = forms.BooleanField(label="Trash",required=False)
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
    episodes=Episode.objects.filter(id__gt=episode_no,location__show=episode.location.show).order_by('id')
    if episodes: nextepisode=episodes[0]
    else: nextepisode=episode

    cuts = Cut_List.objects.filter(episode=episode).order_by('raw_file__trash','raw_file__start')

    clrfFormSet = formset_factory(clrfForm, extra=0)
    if request.method == 'POST': 
        clrfformset = clrfFormSet(request.POST) 
        if clrfformset.is_valid(): 
            for form in clrfformset.forms:
                cl=get_object_or_404(Cut_List,id=form.cleaned_data['clid'])
                cl.raw_file.trash=form.cleaned_data['trash']
                cl.raw_file.comment=form.cleaned_data['rf_comment']
                cl.raw_file.save()
                if form.cleaned_data['delete']:
                    cl.delete()
                else:
                    cl.sequence=form.cleaned_data['sequence']
                    cl.start=form.cleaned_data['start']
                    cl.end=form.cleaned_data['end']
                    cl.comment=form.cleaned_data['cl_comment']
                    cl.save()

            # if trash got touched, need to requery to get things in the right order.  I think.
            cuts = Cut_List.objects.filter(episode=episode).order_by('raw_file__trash','raw_file__start')
            # return HttpResponseRedirect('/thanks/') # Redirect after POST
        else:
            print clrfformset.errors
    else:
        # init data with things in the queryset that need editing
        # this part seems to work.
        init = [{'clid':cut.id,
                'trash':cut.raw_file.trash,
                'sequence':cut.sequence,
                'start':cut.start, 'end':cut.end,
                'cl_comment':cut.comment, 'rf_comment':cut.raw_file.comment,
        } for cut in cuts]
        clrfformset = clrfFormSet(initial=init)


# If all the dates are the same, don't bother displaying them
    talkdate = episode.start.date()
    same_dates = talkdate==episode.end.date()
    if same_dates:
        for cut in cuts:
            # cut.raw_file.dur=cut.raw_file.durationhms()
            same_dates = same_dates and \
               talkdate==cut.raw_file.start.date()==cut.raw_file.end.date()

    return render_to_response('episode.html',
        {'episode':episode,
        'nextepisode':nextepisode,
        'same_dates':same_dates,
        'clrffs':zip(cuts,clrfformset.forms),
        'clrfformset':clrfformset,
        },
    	context_instance=RequestContext(request) )
    	
