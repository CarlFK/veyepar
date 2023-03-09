from django.db import models

from main.models import Show


class VolunteerShow(models.Model):
    """
    Indicator of which shows volunteers should be working to process
    """
    show = models.OneToOneField(Show, on_delete=models.CASCADE)
    processing = models.BooleanField(default=True, help_text="Indicates that " +
                                     "volunteers will be able to see this on " +
                                     "the list page for shows")
