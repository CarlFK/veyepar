from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

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
    

class EpisodeReview(TemplateView):
    """
    Simplified reviewing interface for volunteers
    """
    template_name = "episode_review.html"
    
    def get_context_data(self, **kwargs):
        episode = get_object_or_404(Episode, slug=kwargs.get('episode_slug'), 
                                    show__slug=kwargs.get('show_slug'))
        edit_key = kwargs.get('edit_key')
        if edit_key and not episode.edit_key == edit_key:
            raise Http404
        
        # episode
        # show
        # same_dates (start and end time of episode)
        # comment_form
        # video_form
        return {"episode": episode,
                "show": episode.show,
                "same_dates": self._same_dates(episode.start, episode.end)}
    
    def post(self, request, *args, **kwargs):
        from django.http import HttpResponse
        return HttpResponse("Posted")
    
    def _same_dates(self, start, end):
        return not(start is None or end is None) and start.date() == end.date()