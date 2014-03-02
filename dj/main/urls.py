from django.conf.urls.defaults import url, patterns

# from django.views.generic import list_detail

from views import *

# client_list={"queryset": Client.objects.all(), }
#    "template_object_name": "client_list" }

urlpatterns = patterns(
    'main.views',
    url(r'^$', main, name='main'),
    url(r'clients/$', clients, name='clients'),
    url(r'locations/$', 'locations', name='locations'),
    url(r'C/(?P<client_slug>\w+)/$', client, name='client'),
    url(r'^C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/$',
         episodes, name='episode_list'),
    url(r'raw_file/(?P<raw_file_id>\w+)/$', raw_file, name='raw_file'),

    url(r'approve/(?P<episode_id>\w+)/(?P<episode_slug>\w+)/(?P<edit_key>\w+)/$', approve_episode, name='approve_episode'),
    url(r'E/edit/(?P<episode_id>\w+)/(?P<episode_slug>\w+)/(?P<edit_key>\w+)/$', episode, name='episode'),

    # url(r'state/(?P<state>\w+)/$', episode_list, name='episode_list'),
    url(r'script/(?P<script>\w+)/$', episodes_script, name='episodes_script'),
    
    
    # url(r'^client/(?P<client_slug>[\w\-]+)/(?P<show_slug>[\w\-]+)/$', episodes, name='episode_list'),

    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/L/(?P<location_slug>[\w\-]+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/L/(?P<location_slug>[\w\-]+)/D/(?P<start_day>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/D/(?P<start_day>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>\w+)/S/(?P<show_slug>\w+)/L/(?P<location_slug>[\w\-]+)/D/(?P<start_day>\w+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    url(r'E/(?P<episode_id>\d+)/$', episode, name='episode'),
    url(r'E/(?P<episode_id>\d+)/claim_lock/$', claim_episode_lock),
)
urlpatterns += patterns(
    '',
    url(r'meeting_announcement/(?P<show_id>\w+)/$', 
        meet_ann, 
        name='meet_ann'),
    url(r'show_stats/(?P<show_id>\w+)/$', show_stats, name='show_stats'),
    url(r'show_anomalies/(?P<show_id>\w+)/$', 
        show_anomalies, name='show_anomalies'),

    url(r'schedule/(?P<show_id>\w+)/(?P<show_slug>\w+)_schedule.html$', 
        schedule, 
        name='schedule', kwargs={'template_name':'schedule.html'}),
    url(r'schedule/(?P<show_id>\w+)/(?P<show_slug>\w+)_schedule.iframe$', 
        schedule, 
        name='schedule.iframe', kwargs={'template_name':'schedule.iframe'}),

    url(r'play_list/(?P<show_id>\w+)/L/(?P<location_slug>[\w+\-]+)/.*$', 
        play_list, 
        name='play_list'),
    url(r'play_list/(?P<show_id>\w+)/.*$', 
        play_list, 
        name='play_list'),
    url(r'raw_list/(?P<episode_id>\w+)/.*$', 
        raw_play_list, 
        name='raw_list'),
    url(r'enc_list/(?P<episode_id>\w+)/.*$', 
        enc_play_list, 
        name='enc_list'),
    url(r'pub_play/.*', public_play_list, name='public_play_list'),

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
    url(r'overlaping_files/(?P<show_id>\w+)/$', overlaping_files,
        name='overlaping_files'),

    url(r'raw_file_audio/$', raw_file_audio, name='raw_file_audio'),

    url(r'orphan_dv/(?P<show_id>\w+)/$', orphan_dv,
        name='orphan_dv'),
    url(r'dv_set/(?P<location_slug>[\w+\-]+)/(?P<start_date>[\w+\-]+)/$', 
        dv_set, name='dv_set'),

    url(r'episode_logs/(?P<episode_id>\d+)/$', episode_logs, name='episode_logs'),

    url(r'(?P<rfxml>\w+)/(?P<show_id>\w+)/(?P<episode_id>\w+)/.*$', 
        episode_pdfs, name='pdf'),

    url(r'title_slides/(?P<show_id>\w+)/', 
        title_slides, name='title_slides'),

    url(r'(?P<rfxml>\w+)/(?P<show_id>\w+)/.*$', 
        episode_pdfs, name='pdfs'),

    url(r'tests', tests, name='tests'),

)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

