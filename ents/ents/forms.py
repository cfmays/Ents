from django.forms import ModelForm
from django import forms
from .models import Enrichment

class test(forms.ModelForm):
    model = Enrichment


class CreateEnrichmentForm(forms.ModelForm):

    class Meta:
        model = Enrichment
        fields = ('name', 'photo', 'keywords')
        enctype="multipart/form-data"