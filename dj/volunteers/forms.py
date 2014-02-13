from django import forms

from main.models import Cut_List, Episode


class EpisodeCommentForm(forms.ModelForm):
    """
    A simplified form to handle Episode comments on the volunteer workflow page.
    """
    state = forms.ChoiceField(choices=((1, 'Save and Keep Editing'), 
                                       (2, 'Ready to Encode'),
                                       (0, 'This Episode is Borked')), 
                              widget=forms.RadioSelect(),
                              label="Resolution")
    
    class Meta:
        model = Episode
        fields = ['id', 'comment', 'state']
        exclude = ['show']
        
    def __init__(self, *args, **kwargs):
        super(EpisodeCommentForm, self).__init__(*args, **kwargs)
        self.fields['comment'].help_text = None

        
class SimplifiedCutListForm(forms.ModelForm):
    """
    A really simplified form for volunteers to edit Cut_List instances
    """
    apply = forms.ChoiceField(choices=((True, 'Use this video'), (False, 'Ignore')), 
                              widget=forms.RadioSelect())
    
    class Meta:
        model = Cut_List
        fields = ['id', 'apply']
    
    def __init__(self, *args, **kwargs):
        instance = kwargs.get('instance')
        if instance:
            if not kwargs.get('initial'):
                kwargs['initial'] = {}
            kwargs['initial']['apply'] = instance.apply and not instance.raw_file.trash
        return super(SimplifiedCutListForm, self).__init__(*args, **kwargs)

    