from django.shortcuts import render
from django.views.generic.edit import CreateView
from .models import Enrichment
from django.shortcuts import redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CreateEnrichmentForm


def index(request):
        return render(request, 'index.html')

class EnrichmentUploadView(CreateView):
    model = Enrichment
    form_class=CreateEnrichmentForm
    #fields = ['name','photo','keywords']
    template_name='enrichmentCreateForm.html'

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))
    

