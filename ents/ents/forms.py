from django.forms import Form
from django import forms
from .models import Enrichment, combined_items_notice

class test(forms.ModelForm):
    model = Enrichment


class CreateEnrichmentForm(forms.ModelForm):

    class Meta:
        model = Enrichment
        fields = ('name', 'photo', 'comments', 'components')
        labels = {
            'comments': 'Comments (optional, shown on every calendar)',
            'components': 'Made of (optional, for a combined item)',
        }
        widgets = {'comments': forms.Textarea(attrs={'rows': 2, 'cols': 60})}

    def clean_components(self):
        components = self.cleaned_data['components']
        notice = combined_items_notice(components)
        if notice:
            raise forms.ValidationError(notice)
        return components
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
    searchString2 = forms.CharField(label = 'and also (optional)', required=False)
    searchString3 = forms.CharField(label = 'and also (optional)', required=False)
    doSearch = forms.BooleanField(label = 'Check to filter, uncheck to reset')
    items = forms.ModelChoiceField(label = 'Select Item',queryset=Enrichment.objects.all(), required=False, widget=EnrichmentSelect)


class ItemPhotoForm(forms.Form):
    photo = forms.ImageField()
