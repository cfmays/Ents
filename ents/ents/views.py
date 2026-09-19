from django.http.response import JsonResponse
from django.shortcuts import render
from .models import Enrichment
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CreateEnrichmentForm, enrichment_items_form
from .settings import MEDIA_URL
from zoo.permissions import supervisor_required


def index(request):
    form = enrichment_items_form()
    return render(request, 'index.html', {'form': form})



@supervisor_required
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
        theItems = Enrichment.objects.filter(name__icontains=theSearchString)
    else:
        theItems = Enrichment.objects.all()
    #print('theItems: ')
    #print(theItems)
    return render(request, 'items_dropdown_list_options.html', {'theItems': theItems})
    
def ajax_get_image_url(request):
    theItemID = request.GET.get('theItem')
    if not theItemID:
        return JsonResponse({'theURL': ''})
    results = Enrichment.objects.all().filter(id=theItemID)
    if not results:
        return JsonResponse({'theURL': ''})
    return JsonResponse({'theURL': f"{MEDIA_URL}{results[0].photo.name}"})
