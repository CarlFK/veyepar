from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from volunteers.views import *


urlpatterns = patterns('',
    #(r'^$', login_required(ShowsInProcessing.as_view()), {}, 'volunteer_show_list'),
    #(r'^(?P<show_slug>\w+)/$', login_required(ShowReview.as_view()), {}, 'volunteer_show_review'),
    (r'^unbork/(?P<episode_id>\d+)/$', login_required(UnborkEpisode.as_view()), {}, 'volunteer_unbork'),
    (r'^unbork/(?P<episode_id>\d+)/(?P<edit_key>\w+)/$', UnborkEpisode.as_view(), {}, 'guest_unbork'),
    (r'^(?P<show_slug>\w+)/(?P<episode_slug>\w+)/$', login_required(EpisodeReview.as_view()), {}, 'volunteer_episode_review'),
    (r'^(?P<show_slug>\w+)/(?P<episode_slug>\w+)/(?P<edit_key>\w+)/$', EpisodeReview.as_view(), {}, 'guest_episode_review'),
)
