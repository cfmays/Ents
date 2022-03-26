from django.forms import Form
from django import forms
from .models import Enrichment, KeyWord

class test(forms.ModelForm):
    model = Enrichment


class CreateEnrichmentForm(forms.ModelForm):

    class Meta:
        model = Enrichment
        # fields = ('name', 'photo', 'keywords')
        fields = ('name', 'photo')
        enctype="multipart/form-data"

class enrichment_items_form(Form):

    # keywords = forms.ModelChoiceField(label='Select Keywords', queryset=KeyWord.objects.all(), hidden=True, required=False)
    searchString = forms.CharField(label = 'Enter search text',required=False)
    items = forms.ModelChoiceField(label = 'Select Item',queryset=Enrichment.objects.all(), required=False)
