from django.forms import Form
from django import forms
from .models import Enrichment

class test(forms.ModelForm):
    model = Enrichment


class CreateEnrichmentForm(forms.ModelForm):

    class Meta:
        model = Enrichment
        fields = ('name', 'photo')
        enctype="multipart/form-data"

class EnrichmentSelect(forms.Select):
    """Select widget that adds a data-thumb attribute so JS can show a thumbnail per option."""

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        option = super().create_option(name, value, label, selected, index, subindex, attrs)
        instance = getattr(value, 'instance', None)
        if instance and instance.photo:
            option['attrs']['data-thumb'] = instance.photo.url
        return option


class enrichment_items_form(Form):

    searchString = forms.CharField(label = 'Enter search text', required=False)
    doSearch = forms.BooleanField(label = 'Check to filter, uncheck to reset')
    items = forms.ModelChoiceField(label = 'Select Item',queryset=Enrichment.objects.all(), required=False, widget=EnrichmentSelect)
