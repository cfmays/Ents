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

    searchString = forms.CharField(label = 'Enter search text', required=False)
    doSearch = forms.BooleanField(label = 'Check to filter, uncheck to reset')
    items = forms.ModelChoiceField(label = 'Select Item',queryset=Enrichment.objects.all(), required=False)
