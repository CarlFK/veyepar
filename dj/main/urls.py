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
    url(r'^C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/$',
        episodes, name='episode_list'),
    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/L/(?P<location_slug>\w+)/$', episodes),
    url(r'E/(?P<episode_no>\d+)/$', episode),
    url(r'E/(?P<episode_no>\d+)/claim_lock/$', claim_episode_lock),
)
urlpatterns += patterns(
    '',
    url(r'meeting_announcement/(?P<show_id>\w+)/$', 
        meet_ann, 
        name='meet_ann'),
    url(r'play_list/(?P<show_id>\w+)/.*$', 
        play_list, 
        name='play_list'),
    url(r'raw_list/(?P<episode_id>\w+)/.*$', 
        raw_play_list, 
        name='raw_list'),
    url(r'enc_list/(?P<episode_id>\w+)/.*$', 
        enc_play_list, 
        name='enc_list'),
    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+).json$', 
        eps_xfer,
        name='eps_xfer'),

    url(r'U/user.json$', 
        ajax_user_lookup,
        name='ajax_user_lookup'),
    url(r'Ux/$', 
        ajax_user_lookup_form,
        name='ajax_user_lookup_form'),

    url(r'overlaping_episodes/(?P<show_id>\w+)/$', overlaping_episodes,
        name='overlaping_episodes'),
    url(r'recording_sheets/(?P<show_id>\w+)/.*$', recording_sheets,
        name='recording_sheets'),

    url(r'tests', tests, name='tests'),

)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

