# volunteers/urls.py

from django.conf.urls import url
from django.contrib.auth.decorators import login_required

from volunteers.views import *


urlpatterns = [
    #(r'^$', login_required(ShowsInProcessing.as_view()), {}, 'volunteer_show_list'),
    #(r'^(?P<show_slug>\[-\w]+)/$', login_required(ShowReview.as_view()), {}, 'volunteer_show_review'),
    url(r'^more_videos/(?P<episode_id>\d+)/(?P<slop>\d+)/$', login_required(ExpandCutList.as_view()), {}, 'volunteer_expand_cutlist'),
    url(r'^more_videos/(?P<episode_id>\d+)/(?P<slop>\d+)/(?P<edit_key>\w+)/$', ExpandCutList.as_view(), {}, 'guest_expand_cutlist'),
    url(r'^reopen/(?P<episode_id>\d+)/$', login_required(ReopenEpisode.as_view()), {}, 'volunteer_reopen'),
    url(r'^reopen/(?P<episode_id>\d+)/(?P<edit_key>\w+)/$', ReopenEpisode.as_view(), {}, 'guest_reopen'),
    url(r'^(?P<show_slug>[-\w]+)/(?P<episode_slug>[-\w]+)/$', login_required(EpisodeReview.as_view()), {}, 'volunteer_episode_review'),
    url(r'^(?P<show_slug>[-\w]+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', EpisodeReview.as_view(), {}, 'guest_episode_review'),
    url(r'^(?P<show_slug>[-\w]+)/(?P<episode_slug>[-\w]+)/$', login_required(EpisodeReview.as_view()), {'advanced': True}, 'volunteer_episode_review_advanced'),
    url(r'^(?P<show_slug>[-\w]+)/(?P<episode_slug>[-\w]+)/(?P<edit_key>\w+)/$', EpisodeReview.as_view(), {'advanced': True}, 'guest_episode_review_advanced'),
]
