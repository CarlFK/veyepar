# dj/main/urls.py

from django.conf.urls import patterns, url

# from django.views.generic import list_detail

from .views import *

# client_list={"queryset": Client.objects.all(), }
#    "template_object_name": "client_list" }

urlpatterns = patterns(
    'main.views',
    url(r'^$', main, name='main'),
    url(r'start/$', start_here, name='start_here'),
    url(r'clients/$', clients, name='clients'),
    url(r'locations/$', 'locations', name='locations'),
    url(r'C/(?P<client_slug>[-\w]+)/$', client, name='client'),
    url(r'^C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/$',
         episodes, name='episode_list'),
    url(r'raw_file/(?P<raw_file_id>\w+)/$', raw_file, name='raw_file'),

    url(r'train/(?P<episode_id>\w+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', train, name='train'),
    url(r'approve/(?P<episode_id>\w+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', approve_episode, name='approve_episode'),

    url(r'E/edit/(?P<episode_id>\w+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', episode, name='episode'),

    url(r'state/(?P<state>\w+)/$', episode_list, name='episode_list'),
    url(r'script/(?P<script>\w+)/$', episodes_script, name='episodes_script'),
    
    
    # url(r'^client/(?P<client_slug>[\w\-]+)/(?P<show_slug>[\w\-]+)/$', episodes, name='episode_list'),

    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/L/(?P<location_slug>[\w\-]+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/L/(?P<location_slug>[\w\-]+)/D/(?P<start_day>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/D/(?P<start_day>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/D/(?P<start_day>\w+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/L/(?P<location_slug>[\w\-]+)/D/(?P<start_day>\w+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    url(r'E/(?P<episode_id>\d+)/$', episode, name='episode'),
    url(r'E/(?P<episode_id>\d+)/claim_lock/$', claim_episode_lock),
)
urlpatterns += patterns(
    '',
    url(r'meeting_announcement/(?P<show_id>\w+)/$', 
        meet_ann, 
        name='meet_ann'),
    url(r'show_urls/(?P<show_id>\w+)/$', show_urls, name='show_urls'),
    url(r'show_stats/(?P<show_id>\w+)/$', show_stats, name='show_stats'),
    url(r'show_pipeline/(?P<show_id>\w+)/$', show_pipeline, name='show_pipeline'),
    url(r'processes/(?P<show_id>\w+)/$', processes, name='processes'),
    url(r'show_anomalies/(?P<show_id>\w+)/$', 
        show_anomalies, name='show_anomalies'),

    url(r'schedule/(?P<show_id>\w+)/(?P<show_slug>[-\w]+)_schedule.html$', 
        schedule, 
        name='schedule', kwargs={'template_name':'schedule.html'}),
    url(r'schedule/(?P<show_id>\w+)/(?P<show_slug>[-\w]+)_schedule.iframe$', 
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
    url(r'playlist.m3u$', mk_play_list, name='mk_play_list'),

    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+).csv$', 
        eps_csv,
        name='eps_csv'),
    url(r'E/(?P<ep_id>\d+).json$', 
        ep_json,
        name='ep_json'),
    url(r'M/pyvid_json.urls$', 
        pyvid_jsons,
        name='pyvid_jsons'),
    url(r'veyepar.cfg$',
        veyepar_cfg,
        name='veyepar_cfg'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+).json$', 
        eps_xfer,
        name='eps_xfer'),
    url(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/lanyard.json$', 
        eps_lanynard,
        name='eps_lanynard'),

    url(r'overlapping_episodes/(?P<show_id>\w+)/$', overlapping_episodes,
        name='overlapping_episodes'),
    url(r'overlapping_files/(?P<show_id>\w+)/$', overlapping_files,
        name='overlapping_files'),

    url(r'mini_conf/$', mini_conf,
        name='mini_conf'),

    url(r'raw_file_audio/$', raw_file_audio, name='raw_file_audio'),
    url(r'final_file_audio/$', final_file_audio, name='final_file_audio'),

    url(r'orphan_dv/(?P<show_id>\w+)/', orphan_dv,
        name='orphan_dv'),
    url(r'rf_set/(?P<location_slug>[\w+\-]+)/$', 
        rf_set, name='rf_set'),

    url(r'orphan_img/(?P<show_id>\w+)/$', orphan_img,
        name='orphan_img'),

    url(r'episode_logs/(?P<episode_id>\d+)/$', 
        episode_logs, name='episode_logs'),
    url(r'episode_chaps/(?P<episode_id>\d+)/$', 
        episode_chaps, name='episode_chaps'),

    url(r'(?P<rfxml>\w+)/(?P<show_id>\w+)/(?P<episode_id>\w+)/.*\.pdf$', 
        episode_pdfs, name='pdf'),

    url(r'title_slides/(?P<show_id>\w+)/', 
        title_slides, name='title_slides'),

    url(r'episode_assets/(?P<episode_id>\w+)/', 
        episode_assets, name='episode_assets'),

    url(r'(?P<rfxml>\w+)/(?P<show_id>\w+)/.*\.pdf$', 
        episode_pdfs, name='pdfs'),

    url(r'tests', tests, name='tests'),

)

if False and settings.DEBUG:
    urlpatterns += patterns('',
        (r'^validator/', include('lukeplant_me_uk.django.validator.urls')))

