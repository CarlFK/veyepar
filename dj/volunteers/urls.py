from django.conf.urls.defaults import *
from django.contrib.auth.decorators import login_required

from volunteers.views import *


urlpatterns = patterns('',
    #(r'^$', login_required(ShowsInProcessing.as_view()), {}, 'processing_shows'),
    #(r'^(?P<show_slug>\w+)/$', login_required(ShowReview.as_view()), {}, 'volunteer_show_review'),
    (r'^(?P<show_slug>\w+)/$', login_required(EventReview.as_view()), {}, 'volunteer_event_review'),
)
