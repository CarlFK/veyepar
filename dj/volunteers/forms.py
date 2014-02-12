from django import forms

from main.models import Episode


class EpisodeCommentForm(forms.ModelForm):
    class Meta:
        model = Episode
        fields = ['comment']