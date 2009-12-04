
# forms.py

from django import forms
from main.models import Episode
from django.contrib.admin import widgets                                       


class EpisodeForm(forms.ModelForm):
    class Meta:
        model = Episode

    def __init__(self, *args, **kwargs):
        super(EpisodeForm, self).__init__(*args, **kwargs)
        # self.fields['start'].widget = widgets.AdminSplitDateTime()
        # self.fields['end'].widget = widgets.AdminSplitDateTime()

