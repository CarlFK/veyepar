# forms.py

import re

from django import forms

from main.models import Episode, Location, Mark
from main.models import STATES


class Who(forms.Form):
    locked_by = forms.CharField(max_length=32, required=True,
            label="Please enter your name")

class Location_Form(forms.ModelForm):
    class Meta:
        model = Location
        exclude = ['active',]

class Location_Active_Form(forms.ModelForm):
    class Meta:
        model = Location
        fields = ['active',]

class Episode_Form_Preshow(forms.ModelForm):
    authors = forms.CharField(max_length=255, required=False)
    emails = forms.CharField(max_length=255, required=False)

    def __init__(self, *args, **kwargs):
        locations = kwargs.get('locations', Location.objects.all())
        if 'locations' in kwargs:
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
                  'description',
                  'summary',
                  'tags',
                  'twitter_id',
                  'language',
                  )

class Episode_Form_small(forms.ModelForm):
    class Meta:
        model = Episode
        fields = ('state', 'locked', 'locked_by', 'start', 'duration',
                  'name',
                  'emails',
                  'released',
                  'normalise', 'channelcopy',
                  'thumbnail', 'description', 'comment')

class Episode_Form_Mini(forms.ModelForm):
    emails = forms.CharField(max_length=255, required=False)
    class Meta:
        model = Episode
        fields = ('name',
                  'emails',
                  'description',
                  'comment',
                  'start','end',
                  )
        widgets = {
        	'meails': forms.Textarea(attrs={'cols': 80, 'rows': 2}),
        }


class Episode_Reschedule_Form(forms.ModelForm):

    def mk_dt(self, t, basedate, label):
        # t is time from form in "hh mm ss"

        if t:
            try:
                h,m,s = [int(s) for s in re.split('[ _:]', t)]
                dt = basedate.replace(hour=h, minute=m, second=s)
            except Exception as e:
                print(e)
                raise forms.ValidationError(
                        # django doesn't seem to like this, yet.
			'{label} data bad!: {t} - e:{e}'.format(
                            label=label,
                            t=t,
                            e=e),
			code='invalid',
			params={
                             'label':label,
                             't': t,
                             'e':e.message,
                             },
			)

            marks = Mark.objects.filter(click=dt)
            if not marks:
                raise forms.ValidationError(
                        's datetime not found in marks: {dt}',
                        code='invalid',
                        params={'dt': dt},
                        )
        else:
            dt = None
        return dt

    def clean_start_time(self):
        # t is time in "hh mm ss"
        label = 'start'
        t = self.cleaned_data['start_time']
        basedate = self.instance.start
        dt = self.mk_dt(t, basedate, label)
        return dt

    def clean_end_time(self):
        # t is time in "hh mm ss"
        label = 'end'
        t = self.cleaned_data['end_time']
        basedate = self.instance.end
        dt = self.mk_dt(t, basedate, label)
        return dt

    start_time = forms.CharField(max_length=8,
            required=False,
            widget=forms.TextInput(attrs={'size':'8'}),
            # help = "HH MM SS",
            )

    end_time = forms.CharField(max_length=8,
            required=False,
            widget=forms.TextInput(attrs={'size':'8'}),
            # help = "HH MM SS",
            )


class clrfForm(forms.Form):
    clid = forms.IntegerField(widget=forms.HiddenInput())
    trash = forms.BooleanField(label="Trash",required=False)
    apply = forms.BooleanField(label="Apply",required=False)
    split = forms.BooleanField(label="Split",required=False)
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
    episode_ids  = forms.CharField(max_length=35, required=False,)

class AddEpisodeToRaw(forms.ModelForm):
    class Meta:
        model = Episode
        fields = ('name',
                'duration',
               # 'comment',
                )
    raw_id = forms.IntegerField(widget=forms.HiddenInput())


class MarkPicker(forms.Form):
    apply = forms.BooleanField(label="Apply",required=False)
    click = forms.CharField(max_length=19,label="Start",required=False,
      widget=forms.TextInput(attrs={'size':'15'}))


