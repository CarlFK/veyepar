# veyepar/dj/urls.py

from django.conf import settings
from django.urls import include, re_path

from django.views.generic.base import RedirectView

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.contrib.auth.decorators import login_required

from django.contrib import admin
# admin.autodiscover()

#import django_databrowse as databrowse

import main
from main import urls
from main.models import *

"""
databrowse.site.register(Client)
databrowse.site.register(Show)
databrowse.site.register(Location)
databrowse.site.register(Episode)
databrowse.site.register(Raw_File)
databrowse.site.register(Cut_List)
"""

urlpatterns = [
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs'
    # to INSTALLED_APPS to enable admin documentation:
    # url('^main/approve/2341/Flip_Case_Potentiometer/295432$', RedirectView.as_view(url='/main/approve/2341/Flip_Case_Potentiometer/29543200/')),
    # url('^main/approve/2337/thevenins_theorem/862004$', RedirectView.as_view(url='/main/approve/2337/thevenins_theorem/86200400/')),
    ('^$', RedirectView.as_view(url='/main/')),
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    re_path(r'^admin/', admin.site.urls),
    #(r'^databrowse/(.*)', login_required(databrowse.site.root) ),
    re_path(r'^main/', include('main.urls')),
    re_path(r'^accounts/', include('accounts.urls')),
    # url(r'^my_admin/jsi18n', django.views.i18n.javascript_catalog),
    re_path(r'^volunteers/', include('volunteers.urls')),
    re_path(r'^api/', include('api.urls')),
]

urlpatterns += staticfiles_urlpatterns()
# urlpatterns += patterns('',
# (r'^static/(?P<path>.*)$', 'django.contrib.staticfiles.views.serve',
#        {'document_root': 'static/','show_indexes': True}))

#urlpatterns += patterns('',
# (r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
#(r'^site_media/(?P<path>.*)$', 'django.contrib.staticfiles.views.serve',
#        {'document_root': settings.MEDIA_ROOT,'show_indexes': True}))

