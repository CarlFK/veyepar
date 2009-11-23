# accounts/views.py

from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth import authenticate,login
from django.utils import simplejson 
from django.http import HttpResponse,Http404

from accounts import forms

def auth(username,password):
    ret = {}
    user = authenticate(username=username, password=password)
    if user is not None:
        # correct username and password
        if user.is_active:
            # success
            ret['error_no']=0
            ret['id']=user.id
            ret['username']=user.username
            ret['fullname']=user.get_full_name()
        else:
            # close, but no.
            ret['error_no']=1
            ret['error_text']="Your account is not active."
    else:
        # incorrect username and/or password 
        ret['error_no']=2
        ret['error_text']="Incorrect username and/or password." 

    return ret,user

def logax(request):

    if request.method == 'POST':
        form=forms.LoginForm(request.POST)
        # print form
        if form.is_valid():
            username=form.cleaned_data['username']
            password=form.cleaned_data['password']
            ret,user = auth(username,password)
            if not ret['error_no']:
                l = login(request,user)
        else:
            ret = {'error_no':-1,'error_text':'form error'}
    print ret
    response = HttpResponse(simplejson.dumps(ret,indent=1))
    response['Content-Type'] = 'application/json'
    return response


