import os
import re
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.files import File
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404
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

# Where Charles put the exported photo files for Carolyn to review (dev machine only,
# not part of the deployed app or git). "Temporary" section at the bottom of Manage
# Items reads from here so she can add an item without re-uploading a file she already
# has. Delete this whole block, its two views, the two URLs, and the template section
# once she's gone through them all.
UNASSIGNED_PHOTOS_DIR = Path(settings.BASE_DIR).parent / 'enrichments'
UNASSIGNED_PHOTO_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}


def _unassigned_photo_files():
    """Photo files on disk that aren't the photo of any current item."""
    if not UNASSIGNED_PHOTOS_DIR.is_dir():
        return []
    used_stems = {Path(e.photo.name).stem for e in Enrichment.objects.exclude(photo='')}
    files = []
    for name in sorted(os.listdir(UNASSIGNED_PHOTOS_DIR)):
        stem, ext = os.path.splitext(name)
        if ext.lower() not in UNASSIGNED_PHOTO_EXTENSIONS:
            continue
        if any(u == stem or u.startswith(stem + '_') for u in used_stems):
            continue
        suggested = re.sub(r'[_\-]+', ' ', stem).strip()
        files.append({'filename': name, 'suggested_name': suggested})
    return files


@supervisor_required
def unassigned_photo_preview(request, filename):
    """Streams one file from UNASSIGNED_PHOTOS_DIR, for the thumbnails in that section."""
    if filename != os.path.basename(filename):
        raise Http404
    path = UNASSIGNED_PHOTOS_DIR / filename
    if path.resolve().parent != UNASSIGNED_PHOTOS_DIR.resolve() or not path.is_file():
        raise Http404
    return FileResponse(open(path, 'rb'))


def _add_from_unassigned(request):
    manage = reverse('createView')
    filename = request.POST.get('unassigned_file', '')
    name = ' '.join(request.POST.get('unassigned_name', '').split())
    available = {f['filename'] for f in _unassigned_photo_files()}
    if filename not in available:
        messages.warning(request, 'That photo is no longer available (maybe it was just added by someone else).')
    elif not name:
        messages.warning(request, 'Enter a name for the new item.')
    elif Enrichment.objects.filter(name__iexact=name).exists():
        messages.warning(request, f'An item named "{name}" already exists.')
    else:
        new_item = Enrichment.objects.create(name=name)
        with open(UNASSIGNED_PHOTOS_DIR / filename, 'rb') as fh:
            new_item.photo.save(filename, File(fh), save=True)
        messages.success(request, f'Added {name}.')
        return HttpResponseRedirect(f'{manage}?item={new_item.id}')
    return HttpResponseRedirect(manage)



def count_text(n):
    return f'{n} item' if n == 1 else f'{n} items'


def index(request):
    form = enrichment_items_form()
    count = Enrichment.objects.count()
    form.fields['items'].label = f'Select Item ({count_text(count)})'
    form.fields['items'].empty_label = f'--------- ({count_text(count)})'
    return render(request, 'index.html', {'form': form})



@supervisor_required
def items_master_list_print(request):
    """Printable master list: every item, its thumbnail, and the calendars (if any) it is approved on."""
    items = Enrichment.objects.select_related('category').prefetch_related('asg_assignments__asg').order_by('name')
    rows = [(item, sorted({a.asg.name for a in item.asg_assignments.all()})) for item in items]
    return render(request, 'items_master_list_print.html', {'rows': rows})


def _manage_item(request, item, action):
    """Rename, replace the photo of, set the components of, or delete the selected item; then go back to Manage Items."""
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
    elif action == 'components':
        chosen = Enrichment.objects.exclude(pk=item.pk).filter(pk__in=request.POST.getlist('components'))
        item.components.set(chosen)
        if chosen:
            messages.success(request, f'{item.name} is now a combined item made of {chosen.count()} item(s).')
        else:
            messages.success(request, f'{item.name} is now a normal single item.')
    elif action == 'delete':
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
    if request.method == 'POST' and action in ('rename', 'photo', 'components', 'delete'):
        return _manage_item(request, item, action)
    if request.method == 'POST' and action == 'add_from_unassigned':
        return _add_from_unassigned(request)
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
            'assign_form': assign_form, 'unassigned_photos': _unassigned_photo_files(),
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
        'unassigned_photos': _unassigned_photo_files(),
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
