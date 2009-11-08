from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.contrib import databrowse
from main.models import *

databrowse.site.register(Client)
databrowse.site.register(Show)
databrowse.site.register(Location)
databrowse.site.register(Episode)
databrowse.site.register(Raw_File)
databrowse.site.register(Cut_List)


urlpatterns = patterns('',
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),
    (r'^admin/(.*)', admin.site.root),
    (r'^databrowse/(.*)', databrowse.site.root),
    (r'^main/', include('main.urls')),
    (r'^accounts/', include('accounts.urls')),
)

urlpatterns += patterns('',
(r'^site_media/(?P<path>.*)$', 'django.views.static.serve',
        # {'document_root': '/media/pycon25wed/Videos/veyepar/','show_indexes': True}))
        {'document_root': '/home/carl/Videos/veyepar/','show_indexes': True}))

