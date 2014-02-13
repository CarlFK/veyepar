from django.core import urlresolvers
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import FormView, TemplateView, View

from main.models import Episode, Cut_List
from main.views import mk_cuts
from volunteers.forms import EpisodeResolutionForm, SimplifiedCutListForm


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
    
        cuts = Cut_List.objects.filter(episode=episode
                              ).order_by('sequence','raw_file__start','start')
        if not cuts:
            cuts = mk_cuts(episode)

        return self._context(episode, edit_key,
                             EpisodeResolutionForm(instance=episode),
                             self._cutlist_formset()(queryset=cuts))
    
    def post(self, request, *args, **kwargs):
        episode = get_object_or_404(Episode, slug=kwargs.get('episode_slug'), 
                                    show__slug=kwargs.get('show_slug'))
        edit_key = self._check_edit_key(episode)
        
        comment_form = EpisodeResolutionForm(instance=episode, data=request.POST)
        video_formset = self._cutlist_formset()(data=request.POST)
        
        if comment_form.is_valid() and video_formset.is_valid():
            comment_form.save()
            video_formset.save()
            return HttpResponseRedirect(self._redirect_url(episode, edit_key) +
                                        "#step-3")
        
        return self.render_to_response(self._context(episode, edit_key, 
                                                     comment_form, video_formset))
    
    def _context(self, episode, edit_key, comment_form, video_formset):
        return {"episode": episode,
                "show": episode.show,
                "same_dates": self._same_dates(episode.start, episode.end),
                "edit_key": edit_key,
                "comment_form": comment_form,
                "video_formset": video_formset}
    
    def _cutlist_formset(self):
        return modelformset_factory(Cut_List, form=SimplifiedCutListForm, extra=0)
    
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


class ExpandCutList(FormView):
    pass
 

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
        