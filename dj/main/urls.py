from django.conf.urls.defaults import *
from django.views.generic import list_detail

from views import *

client_list={"queryset": Client.objects.all(), }
#    "template_object_name": "client_list" }

urlpatterns = patterns('',
    (r'^$', main),
    (r'clients/$', list_detail.object_list, client_list),
    (r'C/(?P<client_slug>\w+)/$', client),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/$', client_shows),
    (r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+).json$', eps_xfer ),
    (r'E/(?P<episode_no>\d+)/$', episode),)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

