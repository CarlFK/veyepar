from django.conf.urls.defaults import url, patterns

from django.views.generic import list_detail

from views import *

# client_list={"queryset": Client.objects.all(), }
#    "template_object_name": "client_list" }

urlpatterns = patterns('main.views',
    url(r'^$', main, name='main'),
    url(r'clients/$', clients, name='clients'),
    url(r'locations/$', 'locations', name='locations'),
    url(r'C/(?P<client_slug>\w+)/$', client, name='client'),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/$', episodes),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/L/(?P<location_slug>\w+)/$', episodes),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+).json$', eps_xfer ),
    (r'E/(?P<episode_no>\d+)/$', episode),

)
urlpatterns += patterns(
    '',
    url(r'meeting_announcement/(?P<show_id>\w+)/$', 
        meet_ann, 
        name='meet_ann'),
    url(r'overlaping_episodes/(?P<show_id>\w+)/$', overlaping_episodes,
        name='overlaping_episodes'),
)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

