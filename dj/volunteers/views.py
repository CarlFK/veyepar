from django.views.generic import TemplateView


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