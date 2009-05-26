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

from main.models import Client,Show,Location,Episode

def main(request):
    return render_to_response('main.html',
        context_instance=RequestContext(request) )

def client(request,client_slug=None):
    client=get_object_or_404(Client,slug=client_slug)
    shows=Show.objects.filter(client=client)
    return render_to_response('client.html',
        {'client':client,'shows':shows},
       context_instance=RequestContext(request) )

def get_dv_files(path):
    file_names=os.listdir(path)
    files=[{'name':n} for n in file_names]
    files=[]
    for file_name in os.listdir(path):
        d={'name':file_name,
           'size':os.path.getsize("%s/%s"%(path,file_name))
          }
        files.append(d)
    return files

def show(request,client_slug=None,show_slug=None):
    client=get_object_or_404(Client,slug=client_slug)
    show=get_object_or_404(Show,client=client,slug=show_slug)
    locations=Location.objects.filter(show=show)
    episodes=Episode.objects.filter(location__show=show)
    files=get_dv_files('/home/juser/temp/clojure/2009-may-meeting/sullys/dv')
    return render_to_response('show.html',
        {'client':client,'show':show,
          'locations':locations,'episodes':episodes,
          'files':files},
	context_instance=RequestContext(request) )
    	
