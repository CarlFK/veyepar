from django import forms
from django.forms.models import BaseModelFormSet

from main.models import Cut_List, Episode, Raw_File


class CutListExpansionForm(forms.ModelForm):
    """
    A way for volunteers to find additional Raw_Files and create Cut_Lists
    from them
    """
    apply = forms.ChoiceField(choices=((True, 'Use this video'), (False, 'Ignore')), 
                              widget=forms.RadioSelect())
    
    class Meta:
        model = Raw_File
        fields = ['id', 'apply']
        
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        instance = kwargs.get('instance')
        if instance:
            if not kwargs.get('initial'):
                kwargs['initial'] = {}
            kwargs['initial']['apply'] = False
        return super(CutListExpansionForm, self).__init__(*args, **kwargs)
    
    def save(self, *args, **kwargs):
        import pdb; pdb.set_trace()
        

class CutListExpansionFormSet(BaseModelFormSet):
    form = CutListExpansionForm
    
    def __init__(self, parent, *args, **kwargs):
        self.parent = parent
        super(CutListExpansionFormSet, self).__init__(*args, **kwargs)
    
    def _construct_forms(self):
        # overriding to pass parent obj to child form
        self.forms = []
        for i in xrange(min(self.total_form_count(), self.absolute_max)):
            self.forms.append(self._construct_form(i, parent=self.parent))


class EpisodeResolutionForm(forms.ModelForm):
    """
    A simplified form to handle Episode comments and state on the volunteer 
    episode review page.
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
        super(EpisodeResolutionForm, self).__init__(*args, **kwargs)
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
    
    def save(self, *args, **kwargs):
        obj = super(SimplifiedCutListForm, self).save(*args, **kwargs)
        # raw files that are being included shouldn't be trashed
        if obj.apply and obj.raw_file.trash:
            obj.raw_file.trash = False
            obj.raw_file.save()
        return obj

    