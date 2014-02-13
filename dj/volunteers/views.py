from django.core import urlresolvers
from django.forms.models import modelformset_factory
from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView, View

from main.models import Episode, Cut_List
from main.views import mk_cuts
from volunteers.forms import EpisodeCommentForm, SimplifiedCutListForm


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
    
        cuts = Cut_List.objects.filter(episode=episode
                              ).order_by('sequence','raw_file__start','start')
        if not cuts:
            cuts = mk_cuts(episode)
            
        

        # insert 'advanced' into context
        '''
        

    # If this episode doesn't have a cut list yet, try to create one.
    if not cuts:
        cuts = mk_cuts(episode)

    if cuts:
        offset =  abs( cuts[0].raw_file.start - episode.start )
    else:
        offset = None

    # start times of chapters (included cuts)
    start_chap = (0,"00:00") # frame, timestamp
    chaps,frame_total = [],0 
    for cut in cuts:
        if cut.apply:
            frame_total+=int(cut.duration())
            end_chap = (int(frame_total*29.27), "%s:%02i:%02i" %  
              (frame_total//3600, (frame_total%3600)//60, frame_total%60) )
            chaps.append((start_chap,end_chap,cut))
            # setup for next chapter
            start_chap=end_chap
        else:
            chaps.append(('',''))

    clrfFormSet = formset_factory(clrfForm, extra=0)
    episode_form = Episode_Form_small(instance=episode) 
        # init data with things in the queryset that need editing
        # this part seems to work.
        init = [{'clid':cut.id,
                'trash':cut.raw_file.trash,
                'sequence':cut.sequence,
                'start':cut.start, 'end':cut.end,
                'apply':cut.apply,
                'cl_comment':cut.comment, 'rf_comment':cut.raw_file.comment,
        } for cut in cuts]
        clrfformset = clrfFormSet(initial=init)

    # blank out previous valuse so we don't keep adding the same thing
    add_cutlist_to_ep=Add_CutList_to_Ep(initial = {'sequence':1})
        '''
        
        return self._context(episode, edit_key,
                             EpisodeCommentForm(instance=episode),
                             self._cutlist_formset()(queryset=cuts))
    
    def post(self, request, *args, **kwargs):
        episode = get_object_or_404(Episode, slug=kwargs.get('episode_slug'), 
                                    show__slug=kwargs.get('show_slug'))
        edit_key = self._check_edit_key(episode)
        
        comment_form = EpisodeCommentForm(instance=episode, data=request.POST)
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
        