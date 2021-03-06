from operator import truediv
from os import name
from django.http.response import JsonResponse
from django.shortcuts import render
from django.views.generic.edit import CreateView
from .models import Enrichment
from django.shortcuts import redirect
from django.contrib.auth import logout, login
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CreateEnrichmentForm, enrichment_items_form
from .settings import MEDIA_URL


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

    
def ajax_load_searchstring_items(request):
    #print (request)
    #import ipdb; ipdb.set_trace()
    
    theSearchString=request.GET.get('theSearchString')
    theDoSearch=request.GET.get('theDoSearch')
    #print('theDoSearch; ' + theDoSearch)
    #print('theSearchString: ' + theSearchString)
    if (theDoSearch == 'true'):
        theItems = list(Enrichment.objects.values('id','name').filter(name__icontains=theSearchString))
    else:
        theItems = list(Enrichment.objects.values('id','name').all())
    #print('theItems: ')
    #print(theItems)
    return render(request, 'items_dropdown_list_options.html', {'theItems': theItems})
    
def ajax_load_items(request):
    #print (request)
    #import ipdb; ipdb.set_trace()
    
    theKeyWord=request.GET.get('theKeyWord')
    theItems = list(Enrichment.objects.values('id','name').filter(keywords__in=theKeyWord))
    return render(request, 'items_dropdown_list_options.html', {'theItems': theItems})

def ajax_get_image_url(request):
    theItemID = request.GET.get('theItem')
    # print('theItemID: ' + theItemID)
    results = Enrichment.objects.all().filter(id=theItemID)
    return JsonResponse({'theURL': f"{MEDIA_URL}{results[0].photo.name}"})

from django.urls import path


