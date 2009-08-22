from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from django.core.paginator import Paginator, InvalidPage

from django import forms
from django.forms import ModelForm

from django.db.models import Q

from datetime import datetime
from datetime import timedelta
import os

from main.models import Client,Show,Location,Episode,Cut_List

class Cut_ListRaw_FileForm(forms.Form):
    trash = forms.BooleanField(label="Trash")
    sequence = forms.IntegerField(label="Sequence",
      widget=forms.TextInput(attrs={'size':'3'}))
    start = forms.CharField(max_length=12,label="Start",
      help_text = "offset from start in h:m:s or frames, blank for start",
      widget=forms.TextInput(attrs={'size':'9'}))
    end = forms.CharField(max_length=12,label="End",
      help_text = "offset from start in h:m:s or frames, blank for end",
      widget=forms.TextInput(attrs={'size':'9'}))
    rf_comment = forms.CharField(label="Raw_File comment",
      widget=forms.Textarea(attrs={'rows':'2','cols':'20'}))
    cl_comment = forms.CharField(label="Cut_List comment",
      widget=forms.Textarea(attrs={'rows':'2','cols':'20'}))


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
 
def episode(request,episode_no):
    episode=get_object_or_404(Episode,id=episode_no)
    cuts = Cut_List.objects.filter(episode=episode).order_by('raw_file__start')
    clrfform = Cut_ListRaw_FileForm()

# If all the dates are the same, don't bother displaying them
    talkdate = episode.start.date()
    same = talkdate==episode.end.date()
    if same:
        for cut in cuts:
            # cut.raw_file.dur=cut.raw_file.durationhms()
            same = same and \
               talkdate==cut.raw_file.start.date()==cut.raw_file.end.date()

    return render_to_response('episode.html',
        {'episode':episode,
        'same_dates':same,
        'cuts':cuts, 
        'clrfform':clrfform, 
        },
	context_instance=RequestContext(request) )
    	
