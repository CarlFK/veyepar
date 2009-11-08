from django.conf.urls.defaults import *
from django.views.generic import list_detail

from views import *

# client_list={"queryset": Client.objects.all(), }
#    "template_object_name": "client_list" }

urlpatterns = patterns('',
    (r'^$', main),
    (r'clients/$', clients),
    (r'C/(?P<client_slug>\w+)/$', client),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/$', locations),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/E/$', episodes),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/L/(?P<location_slug>\w+)/$', episodes),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+).json$', eps_xfer ),
    (r'E/(?P<episode_no>\d+)/$', episode),

)
urlpatterns += patterns(
    '',
    url(r'meeting_announcement/(?P<location_id>\w+)/$', 
        meet_ann, 
        name='meet_ann'),
)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

