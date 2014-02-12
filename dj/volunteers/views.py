from django.core import urlresolvers
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from main.models import Episode


class ShowsInProcessing(TemplateView):
    """
    Lists all Shows that have a VolunteerShow associated with it that are 
    currently processing
    """
    template_name = "processing_shows.html"
    
    def get_context_data(self, **kwargs):
        return {}

    
class ShowReview(TemplateView):
    template_name = "show_review.html"
    

class EditKeyMixin(object):
    def _check_edit_key(self, episode):
        edit_key = self.kwargs.get('edit_key')
        if edit_key and not episode.edit_key == edit_key:
            raise Http404
        return edit_key
    
    def _redirect_url(self, episode, edit_key):
        if edit_key:
            return urlresolvers.reverse('guest_episode_review',
                                        kwargs={'show_slug': episode.show.slug,
                                                'episode_slug': episode.slug,
                                                'edit_key': edit_key})
        else:
            return urlresolvers.reverse('volunteer_episode_review',
                                        kwargs={'show_slug': episode.show.slug,
                                                'episode_slug': episode.slug})


class EpisodeReview(TemplateView, EditKeyMixin):
    """
    Simplified reviewing interface for volunteers
    """
    template_name = "episode_review.html"
    
    def get_context_data(self, **kwargs):
        episode = get_object_or_404(Episode, slug=kwargs.get('episode_slug'), 
                                    show__slug=kwargs.get('show_slug'))
        edit_key = self._check_edit_key(episode)

        # comment_form
        # video_form
        return {"episode": episode,
                "show": episode.show,
                "same_dates": self._same_dates(episode.start, episode.end),
                "edit_key": edit_key}
    
    def post(self, request, *args, **kwargs):
        from django.http import HttpResponse
        return HttpResponse("Posted to Episode Review")
    
    def _same_dates(self, start, end):
        return not(start is None or end is None) and start.date() == end.date()


class ReopenEpisode(View, EditKeyMixin):
    def post(self, request, *args, **kwargs):
        self.kwargs = kwargs
        
        episode = get_object_or_404(Episode, id=kwargs.get('episode_id'))
        edit_key = self._check_edit_key(episode)
        episode.state = 1
        episode.save()
        
        return HttpResponseRedirect(self._redirect_url(episode, edit_key))
        