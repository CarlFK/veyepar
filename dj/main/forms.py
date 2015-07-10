
# forms.py

from django import forms
from main.models import Episode, Location
# from django.contrib.admin import widgets


class Who(forms.Form):
    locked_by = forms.CharField(max_length=32, required=True,
            label="Please enter your name")

class Episode_Form(forms.ModelForm):
    exclude=[]
    class Meta:
        model = Episode

class Episode_Form_Preshow(forms.ModelForm):
    authors = forms.CharField(max_length=255, required=False)
    emails = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        locations = kwargs.get('locations', Location.objects.all())
        if kwargs.has_key('locations'):
           del kwargs['locations']
        super(Episode_Form_Preshow, self).__init__(*args, **kwargs)
        self.fields['location']._set_choices([(l.id, l.name) for l in locations])

    class Meta:
        model = Episode
        fields = ('sequence',
                  'name', 'slug',
                  'show','location',
                  'start', 'duration',
                  'authors',
                  'emails',
                  'released',
                  'description', 'tags')

class Episode_Form_small(forms.ModelForm):
    class Meta:
	model = Episode
        fields = ('state', 'locked', 'locked_by', 'start', 'duration',
                  'emails',
                  'released',
                  'normalise', 'channelcopy',
                  'thumbnail', 'description', 'comment')

class clrfForm(forms.Form):
    clid = forms.IntegerField(widget=forms.HiddenInput())
    trash = forms.BooleanField(label="Trash",required=False)
    apply = forms.BooleanField(label="Apply",required=False)
    split = forms.BooleanField(label="Spill",required=False)
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

class Add_CutList_to_Ep(forms.Form):
    rf_filename = forms.CharField(max_length=132,required=False,
      help_text = "root is .../show/dv/location/, example: 2013-03-13/13:13:30.dv" )
    sequence = forms.IntegerField(label="Sequence",required=False,
      widget=forms.TextInput(attrs={'size':'3','class':'suSpinButton'}))
    getit = forms.BooleanField(label="get this", required=False,
            help_text="check and save to add this")

class AddImageToEp(forms.Form):
    image_id = forms.IntegerField(widget=forms.HiddenInput())
    episode_id  = forms.IntegerField(required=False,)
 
