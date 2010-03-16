
# forms.py

from django import forms
from main.models import Episode
from django.contrib.admin import widgets                                       


class Episode_Form(forms.ModelForm):
    class Meta:
        model = Episode

class Episode_Form_small(forms.ModelForm):
    class Meta:
	model = Episode
        fields = ('state', 'locked', 'locked_by', 'normalise', 'channelcopy',
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

