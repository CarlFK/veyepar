
# forms.py

from django import forms
from main.models import Episode, Location
from django.contrib.admin import widgets                                       


class Episode_Form(forms.ModelForm):
    class Meta:
        model = Episode

class Episode_Form_Preshow(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        locations = kwargs.get('locations', Location.objects.all())
        if kwargs.has_key('locations'):
           del kwargs['locations']
        super(Episode_Form_Preshow, self).__init__(*args, **kwargs)
        self.fields['location']._set_choices([(l.id, l.name) for l in locations])

    class Meta:
        model = Episode
        fields = (
                  'name', 'slug', 
                  'show','location', 
                  'start', 'duration', 
                  'sequence',
                  'authors', 
                  'emails',
                  'released', 
                  'description', 'tags')

class Episode_Form_small(forms.ModelForm):
    class Meta:
	model = Episode
        fields = ('state', 'locked', 'locked_by', 'start', 'duration',
                  'normalise', 'channelcopy',
                  'thumbnail', 'description', 'comment')


class clrfForm(forms.Form):
    clid = forms.IntegerField(widget=forms.HiddenInput())
    trash = forms.BooleanField(label="Trash",required=False)
    apply = forms.BooleanField(label="Apply",required=False)
    split = forms.BooleanField(label="Spilt",required=False)
    sequence = forms.IntegerField(label="Sequence",required=False,
      widget=forms.TextInput(attrs={'size':'3','class':'suSpinButton'}))
    start = forms.CharField(max_length=12,label="Start",required=False,
      help_text = "offset from start in h:m:s or frames, blank for start",
      widget=forms.TextInput(attrs={'size':'9'}))
    end = forms.CharField(max_length=12,label="End",required=False,
      help_text = "offset from start in h:m:s or frames, blank for end",
      widget=forms.TextInput(attrs={'size':'9'}))
    rf_comment = forms.CharField(label="Raw_File comment",required=False,
      widget=forms.Textarea(attrs={'rows':'2','cols':'20'}))
    cl_comment = forms.CharField(label="Cut_List comment",required=False,
      widget=forms.Textarea(attrs={'rows':'2','cols':'20'}))

