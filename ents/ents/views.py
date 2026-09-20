from django.contrib import messages
from django.core.files.storage import default_storage
from django.http.response import JsonResponse
from django.shortcuts import render
from .models import Enrichment
from django.contrib.auth import logout
from django.http import HttpResponseRedirect
from django.urls import reverse
from .forms import CreateEnrichmentForm, ItemPhotoForm, enrichment_items_form
from .settings import MEDIA_URL
from zoo.forms import ItemAssignmentForm
from zoo.models import ASGApprovedItem, default_is_food
from zoo.permissions import division_scope, supervisor_required


def count_text(n):
    return f'{n} item' if n == 1 else f'{n} items'


def index(request):
    form = enrichment_items_form()
    count = Enrichment.objects.count()
    form.fields['items'].label = f'Select Item ({count_text(count)})'
    form.fields['items'].empty_label = f'--------- ({count_text(count)})'
    return render(request, 'index.html', {'form': form})



def _manage_item(request, item, action):
    """Rename, replace the photo of, or delete the selected item; then go back to the Manage Items page."""
    manage = reverse('createView')
    if item is None:
        messages.warning(request, 'Choose an item first.')
        return HttpResponseRedirect(manage)
    back = f'{manage}?item={item.id}'

    if action == 'rename':
        name = ' '.join(request.POST.get('name', '').split())
        if not name:
            messages.warning(request, 'An item needs a name.')
        elif Enrichment.objects.filter(name__iexact=name).exclude(pk=item.pk).exists():
            messages.warning(request, f'Another item is already named "{name}".')
        else:
            item.name = name
            item.save()
            messages.success(request, 'Item renamed.')
    elif action == 'photo':
        form = ItemPhotoForm(request.POST, request.FILES)
        if form.is_valid():
            old_photo = item.photo.name
            item.photo.save(form.cleaned_data['photo'].name, form.cleaned_data['photo'], save=True)  # also resizes it
            if old_photo and old_photo != item.photo.name:
                item.photo.storage.delete(old_photo)
            messages.success(request, 'Photo replaced.')
        else:
            messages.warning(request, 'Choose an image file (jpg, png, gif or webp).')
    else:  # delete
        entries = item.calendar_entries.count()
        if entries:
            messages.warning(request, f'{item.name} is used in {entries} calendar entries, so it cannot be deleted.')
        else:
            name, old_photo = item.name, item.photo.name
            item.delete()  # also takes it off the calendars it was approved on
            if old_photo:
                default_storage.delete(old_photo)
            messages.success(request, f'Deleted {name}.')
            return HttpResponseRedirect(manage)
    return HttpResponseRedirect(back)


@supervisor_required
def EnrichmentUploadView(request):
    """Manage Items: pick an existing item to rename / re-photo / delete, or upload a new one."""
    item = Enrichment.objects.filter(pk=request.GET.get('item') or request.POST.get('item') or None).first()
    action = request.POST.get('action')
    assign_form = ItemAssignmentForm(divisions=division_scope(request))
    if request.method == 'POST' and action in ('rename', 'photo', 'delete'):
        return _manage_item(request, item, action)
    if request.method == 'POST' and action == 'add_to_lists':
        assign_form = ItemAssignmentForm(request.POST, divisions=division_scope(request))
        if assign_form.is_valid():
            created = 0
            for chosen in assign_form.cleaned_data['items']:
                for asg in assign_form.cleaned_data['asgs']:
                    _, was_created = ASGApprovedItem.objects.get_or_create(asg=asg, item=chosen, is_food=default_is_food(chosen))
                    created += int(was_created)
            messages.success(request, f'Created {created} new item/calendar list assignment(s).')
            return HttpResponseRedirect(reverse('createView'))
        form = CreateEnrichmentForm()
        return render(request, 'createEnrichment.html', {
            'form': form, 'item': item, 'items': Enrichment.objects.all(), 'calendars': 0, 'entries': 0,
            'assign_form': assign_form,
        })

    if request.method == 'POST':
        form = CreateEnrichmentForm(request.POST, request.FILES)
        if form.is_valid():
            new_item = form.save()
            messages.success(request, f'Added {new_item.name}.')
            return HttpResponseRedirect(f"{reverse('createView')}?item={new_item.id}")  # stay on Manage Items
    else:
        form = CreateEnrichmentForm()
    calendars = entries = 0
    if item:
        calendars = item.asg_assignments.values('asg').distinct().count()
        entries = item.calendar_entries.count()
    return render(request, 'createEnrichment.html', {
        'form': form,
        'item': item,
        'items': Enrichment.objects.all(),
        'calendars': calendars,
        'entries': entries,
        'assign_form': assign_form,
    })

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('index'))

    
def ajax_load_searchstring_items(request):
    theItems = Enrichment.objects.all()
    if request.GET.get('theDoSearch') == 'true':
        # every non-blank search string (up to three) must appear in the name
        for key in ('theSearchString', 'theSearchString2', 'theSearchString3'):
            text = request.GET.get(key, '').strip()
            if text:
                theItems = theItems.filter(name__icontains=text)
    return render(request, 'items_dropdown_list_options.html', {
        'theItems': theItems,
        'count_text': count_text(theItems.count()),
    })

def ajax_get_image_url(request):
    theItemID = request.GET.get('theItem')
    if not theItemID:
        return JsonResponse({'theURL': ''})
    results = Enrichment.objects.all().filter(id=theItemID)
    if not results:
        return JsonResponse({'theURL': ''})
    return JsonResponse({'theURL': f"{MEDIA_URL}{results[0].photo.name}"})
