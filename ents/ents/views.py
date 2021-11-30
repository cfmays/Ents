from django.shortcuts import render
from django.views.generic.edit import CreateView
from .models import Enrichment
from django.shortcuts import redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CreateEnrichmentForm, enrichment_items_form


def index(request):
    form = enrichment_items_form()
    return render(request, 'index.html', {'form': form})



def EnrichmentUploadView(request):
    if request.method == 'POST':
        #print('in POST')
        #print (request)
        form = CreateEnrichmentForm(request.POST, request.FILES)
        #import ipdb; ipdb.set_trace()
        #print('form created')
        if form.is_valid():
            #print('saving form...')
            form.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            #print('form is not valid')
            return render(request, 'createEnrichment.html', {'form':form})

    else:
        #print('in else')
        #print (request)
        form = CreateEnrichmentForm()
        return render(request, 'createEnrichment.html', {'form':form})

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

def EnrichmentUploadView(request):
    if request.method == 'POST':
        form = CreateEnrichmentForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('index'))
        else:
            return render(request, 'createEnrichment.html', {'form':form})

    else:
        form = CreateEnrichmentForm()
        return render(request, 'createEnrichment.html', {'form':form})
    
def ajax_load_items(request):
    print (request)
    #import ipdb; ipdb.set_trace()
    
    theKeyWord=request.GET.get('theKeyWord')
    theItems = list(Enrichment.objects.values('id','name').filter(keywords__in=theKeyWord))
    return render(request, 'items_dropdown_list_options.html', {'theItems': theItems})
