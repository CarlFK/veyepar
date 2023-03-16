# dj/main/urls.py

from django.urls import path, re_path

from .views import *

urlpatterns = [
    path(r'', main, name='main'),
    re_path(r'start/$', start_here, name='start_here'),
    re_path(r'clients/$', clients, name='clients'),
    re_path(r'locations/$', locations, name='locations'),
    re_path(r'C/(?P<client_slug>[-\w]+)/$', client, name='client'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/$',
         episodes, name='episode_list'),
    re_path(r'reschedule/(?P<show_id>\d+)/$',
         episodes_reschedule, name='episodes_reschedule'),
    re_path(r'raw_file/(?P<raw_file_id>\w+)/$', raw_file, name='raw_file'),

    re_path(r'train/(?P<episode_id>\w+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', train, name='train'),
    re_path(r'approve/(?P<episode_id>\w+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', approve_episode, name='approve_episode'),

    re_path(r'.*E/edit/(?P<episode_id>\w+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', episode, name='episode'),

    re_path(r'state/(?P<state>\w+)/$', episode_list, name='episode_list'),
    re_path(r'script/(?P<script>\w+)/$', episodes_script, name='episodes_script'),

    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/L/(?P<location_slug>[\w\-]+)/$', episodes, name='episode_list'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/L/(?P<location_slug>[\w\-]+)/D/(?P<start_day>\w+)/$', episodes, name='episode_list'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/D/(?P<start_day>\w+)/$', episodes, name='episode_list'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/D/(?P<start_day>\w+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/L/(?P<location_slug>[\w\-]+)/D/(?P<start_day>\w+)/s/(?P<state>\w+)/$', episodes, name='episode_list'),

    re_path(r'.*E/(?P<episode_id>\d+)/$', episode, name='episode'),
    re_path(r'.*E/(?P<episode_id>\d+)/claim_lock/$', claim_episode_lock),

    re_path(r'meeting_announcement/(?P<show_id>\w+)/$',
        meet_ann,
        name='meet_ann'),
    re_path(r'show_urls/(?P<show_id>\w+)/$', show_urls, name='show_urls'),
    re_path(r'show_stats/(?P<show_id>\w+)/$', show_stats, name='show_stats'),
    re_path(r'show_pipeline/(?P<show_id>\w+)/$', show_pipeline, name='show_pipeline'),
    re_path(r'show_parameters/(?P<show_id>\w+)/$', show_parameters, name="show_parameters"),
    re_path(r'processes/(?P<show_id>\w+)/$', processes, name='processes'),

    re_path(r'episode_assets/(?P<episode_id>\w+)/(?P<slug>\w+)\.(?P<mode>\w+)',
        episode_assets, name='episode_assets'),

    re_path(r'show_anomalies/(?P<show_id>\w+)/$',
        show_anomalies, name='show_anomalies'),

    re_path(r'schedule/(?P<show_id>\w+)/(?P<show_slug>[-\w]+)_schedule.html$',
        schedule,
        name='schedule', kwargs={'template_name':'schedule.html'}),
    re_path(r'schedule/(?P<show_id>\w+)/(?P<show_slug>[-\w]+)_schedule.iframe$',
        schedule,
        name='schedule.iframe', kwargs={'template_name':'schedule.iframe'}),

    re_path(r'play_list/(?P<show_id>\w+)/L/(?P<location_slug>[\w+\-]+)/.*$',
        play_list,
        name='play_list'),
    re_path(r'play_list/(?P<show_id>\w+)/.*$',
        play_list,
        name='play_list'),
    re_path(r'raw_list/(?P<episode_id>\w+)/.*$',
        raw_play_list,
        name='raw_list'),
    re_path(r'enc_list/(?P<episode_id>\w+)/.*$',
        enc_play_list,
        name='enc_list'),
    re_path(r'pub_play/.*', public_play_list, name='public_play_list'),
    re_path(r'playlist.m3u$', mk_play_list, name='mk_play_list'),

    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+).csv$',
        eps_csv,
        name='eps_csv'),
    re_path(r'E/(?P<ep_id>\d+).json$',
        ep_json,
        name='ep_json'),
    re_path(r'.*M/pyvid_json.urls$',
        pyvid_jsons,
        name='pyvid_jsons'),

    re_path(r'veyepar.cfg/(?P<show_id>\d+)$',
        veyepar_cfg,
        name='veyepar_cfg'),

    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/asset_names.json',
        asset_names,
        name='asset_names'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+).json$',
        eps_xfer,
        name='eps_xfer'),
    re_path(r'C/(?P<client_slug>[-\w]+)/S/(?P<show_slug>[-\w]+)/lanyard.json$',
        eps_lanynard,
        name='eps_lanynard'),

    re_path(r'overlapping_episodes/(?P<show_id>\w+)/$', overlapping_episodes,
        name='overlapping_episodes'),
    re_path(r'overlapping_files/(?P<show_id>\w+)/$', overlapping_files,
        name='overlapping_files'),

    re_path(r'mini_conf/$', mini_conf,
        name='mini_conf'),

    re_path(r'show_list/$', show_list,
        name='show_list'),

    re_path(r'raw_file_audio/$', raw_file_audio, name='raw_file_audio'),
    re_path(r'final_file_audio/$', final_file_audio, name='final_file_audio'),


    re_path(r'mk_episode/(?P<show_id>\w+)/', mk_episode,
        name='mk_episode'),

    re_path(r'orphan_dv/(?P<show_id>\w+)/', orphan_dv,
        name='orphan_dv'),
    re_path(r'rf_set/(?P<location_slug>[\w+\-]+)/$',
        rf_set, name='rf_set'),

    re_path(r'orphan_img/(?P<show_id>\w+)/$', orphan_img,
        name='orphan_img'),

    re_path(r'slugoh/(?P<show_id>\w+)/$', slugoh,
        name='slugoh'),

    re_path(r'episode_logs/(?P<episode_id>\d+)/$',
        episode_logs, name='episode_logs'),
    re_path(r'episode_chaps/(?P<episode_id>\d+)/$',
        episode_chaps, name='episode_chaps'),

    re_path(r'(?P<rfxml>\w+)\.pdf/(?P<show_id>\w+)/(?P<episode_id>\w+)/.*$',
        episode_pdfs, name='pdf'),

    re_path(r'(?P<rfxml>\w+)\.pdf/(?P<show_id>\w+)/.*$',
        episode_pdfs, name='pdfs'),

    re_path(r'title_slides/(?P<show_id>\w+)/',
        title_slides, name='title_slides'),

    re_path(r'util/title_templates/', title_templates, name="title_templates" ),

    re_path(r'tests/$', tests, name='tests'),
    re_path(r'tests/samplespec.rfxml', test_rfxml, name='testrfxml'),
]


