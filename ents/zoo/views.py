import calendar
import re
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.db.models import Count, Prefetch, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from .forms import item_labels_for, AddAnimalChoiceForm, ItemAssignmentForm, TrainingSessionForm, TrainingStringForm, make_calendar_entry_formset
from ents.models import Enrichment
from .models import Division, Behavior, Reinforcer, ASG, ASGApprovedItem, Animal, default_is_food, BehaviorGoal, BehaviorScore, CalendarEntry, Profile, SpecialConcern, String, TrainingAnimal, TrainingSession
from django.utils.http import url_has_allowed_host_and_scheme

from .permissions import available_divisions, division_scope, is_supervisor, supervisor_required, user_can_access_asg, user_can_access_string, user_can_access_training_animal


def _today():
    return date.today()  # a function so tests can pin the date


def _get_accessible_asg(request, asg_id):
    asg = get_object_or_404(ASG, pk=asg_id)
    if not user_can_access_asg(request.user, asg):
        raise PermissionDenied("You don't have access to this calendar.")
    return asg


def _get_accessible_training_animal(request, animal_id):
    animal = get_object_or_404(TrainingAnimal, pk=animal_id)
    if not user_can_access_training_animal(request.user, animal):
        raise PermissionDenied("You don't have access to this animal.")
    return animal


@login_required
def asg_list(request):
    scope = division_scope(request)
    if request.user.is_superuser:
        strings = String.objects.all() if scope is None else String.objects.filter(division__in=scope)
    else:
        strings = String.objects.filter(Q(keepers=request.user) | Q(division__in=scope)).distinct()
    strings = strings.prefetch_related('asgs')
    return render(request, 'zoo/asg_list.html', {'strings': strings, 'can_manage_lists': is_supervisor(request.user)})


# never cached, so Back from the print page shows what was just saved, not an old copy
@login_required
@never_cache
def calendar_tab(request, asg_id, year=None, month=None):
    asg = _get_accessible_asg(request, asg_id)
    today = _today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    days_in_month = calendar.monthrange(year, month)[1]
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    FormSet = make_calendar_entry_formset(asg, year, month)
    queryset = CalendarEntry.objects.filter(asg=asg, date__gte=month_start, date__lte=month_end)

    read_only = (year, month) < (today.year, today.month)  # past months can't be changed

    if request.method == 'POST' and read_only:
        messages.warning(request, f'{_month_label(year, month)} is a past month and is read only.')
        return redirect('zoo:calendar_tab', asg_id=asg.id, year=year, month=month)
    if request.method == 'POST':
        formset = FormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            instances = formset.save(commit=False)
            for instance in instances:
                instance.asg = asg
                if not instance.created_by_id:
                    instance.created_by = request.user
                instance.save()
            messages.success(request, 'Calendar saved.')
            if request.POST.get('print_after'):
                return redirect('zoo:calendar_print', asg_id=asg.id, year=year, month=month)
            return redirect('zoo:calendar_tab', asg_id=asg.id, year=year, month=month)
    else:
        formset = FormSet(queryset=queryset)

    prev_month = (month_start.replace(day=1) - date.resolution).replace(day=1)
    next_month = (month_end + date.resolution)

    labels = item_labels_for(asg) if read_only else {}
    clip = request.session.get('calendar_clipboard')
    clipboard = None
    if clip and clip['asg_id'] == asg.id:
        clipboard = f"{_entries(len(clip['entries']))} from {_month_label(clip['year'], clip['month'])}"

    return render(request, 'zoo/calendar_tab.html', {
        'asg': asg,
        'clipboard': clipboard,
        'can_manage_lists': is_supervisor(request.user),
        'has_animals': asg.animals.exists(),
        'read_only': read_only,
        'read_only_rows': [
            (entry, labels.get(entry.item_id, entry.item.name))
            for entry in queryset.select_related('item', 'animal', 'behavior_goal')
        ] if read_only else [],
        'formset': formset,
        'year': year,
        'month': month,
        'month_name': month_start.strftime('%B %Y'),
        'prev_year': prev_month.year,
        'prev_month': prev_month.month,
        'next_year': next_month.year,
        'next_month': next_month.month,
    })


def _entries(n):
    return f'{n} entry' if n == 1 else f'{n} entries'


def _month_label(year, month):
    return date(year, month, 1).strftime('%B %Y')


@login_required
def calendar_print(request, asg_id, year, month):
    """Printable copy of a month's saved entries (no DO/IO/GBS/Notes columns)."""
    asg = _get_accessible_asg(request, asg_id)
    entries = CalendarEntry.objects.filter(asg=asg, date__year=year, date__month=month).select_related(
        'item', 'animal', 'behavior_goal',
    )
    labels = item_labels_for(asg)
    return render(request, 'zoo/calendar_print.html', {
        'asg': asg,
        'month_name': _month_label(year, month),
        'rows': [(entry, labels.get(entry.item_id, entry.item.name)) for entry in entries],
        'has_animals': asg.animals.exists(),
        'year': year,
        'month': month,
    })


@login_required
@require_POST
def calendar_copy(request, asg_id, year, month):
    """Copy what's on the calendar page (saved or not) without reloading it; replies with JSON."""
    asg = _get_accessible_asg(request, asg_id)
    if 'form-TOTAL_FORMS' in request.POST:
        queryset = CalendarEntry.objects.filter(asg=asg, date__year=year, date__month=month)
        formset = make_calendar_entry_formset(asg, year, month)(request.POST, queryset=queryset)
        if not formset.is_valid():
            problems = []
            for form in formset.forms:
                for errors in form.errors.values():
                    problems += [e for e in errors if e not in problems]
            return JsonResponse({'level': 'warning', 'message': "Can't copy yet. " + ' '.join(problems)})
        rows = [
            (f.cleaned_data['date'], f.cleaned_data.get('animal'), f.cleaned_data['item'], f.cleaned_data.get('behavior_goal'))
            for f in formset.forms
            if f.cleaned_data.get('date') and f.cleaned_data.get('item')
            and (f.cleaned_data['date'].year, f.cleaned_data['date'].month) == (year, month)
        ]
    else:
        rows = [
            (e.date, e.animal, e.item, e.behavior_goal)
            for e in CalendarEntry.objects.filter(asg=asg, date__year=year, date__month=month)
        ]

    if not rows:
        return JsonResponse({'level': 'warning', 'message': f'Nothing to copy: no entries in {_month_label(year, month)}.'})
    request.session['calendar_clipboard'] = {
        'asg_id': asg.id, 'year': year, 'month': month,
        'entries': [
            {'day': d.day, 'animal': animal.id if animal else None, 'item': item.id, 'goal': goal.id if goal else None}
            for d, animal, item, goal in rows
        ],
    }
    what = f'{_entries(len(rows))} from {_month_label(year, month)}'
    return JsonResponse({'level': 'success', 'message': f'Copied {what}.', 'clipboard': what})


@login_required
@require_POST
def calendar_paste(request, asg_id, year, month):
    asg = _get_accessible_asg(request, asg_id)
    clip = request.session.get('calendar_clipboard')
    back = redirect('zoo:calendar_tab', asg_id=asg.id, year=year, month=month)
    today = _today()
    if (year, month) < (today.year, today.month):
        messages.warning(request, f'{_month_label(year, month)} is a past month and is read only.')
        return back
    if not clip:
        messages.warning(request, 'Nothing to paste yet: use Copy on another month first.')
        return back
    if clip['asg_id'] != asg.id:
        source = ASG.objects.filter(pk=clip['asg_id']).first()
        messages.warning(request, f'You copied from {source or "another calendar"}; Paste only works within the same calendar.')
        return back

    days_in_month = calendar.monthrange(year, month)[1]
    approved_items = set(asg.approved_items.values_list('id', flat=True))
    valid_animals = set(asg.animals.values_list('id', flat=True))
    valid_goals = set(asg.behavior_goals.values_list('id', flat=True))
    existing = set(
        CalendarEntry.objects.filter(asg=asg, date__year=year, date__month=month)
        .values_list('date', 'item_id', 'animal_id')
    )

    pasted = 0
    dropped_days = []
    not_approved = 0
    already_there = 0
    for e in clip['entries']:
        if e['day'] > days_in_month:
            dropped_days.append(e['day'])
            continue
        if e['item'] not in approved_items:
            not_approved += 1
            continue
        animal_id = e['animal'] if e['animal'] in valid_animals else None
        key = (date(year, month, e['day']), e['item'], animal_id)
        if key in existing:
            already_there += 1
            continue
        CalendarEntry.objects.create(
            asg=asg, date=key[0], item_id=e['item'], animal_id=animal_id,
            behavior_goal_id=e['goal'] if e['goal'] in valid_goals else None,
            created_by=request.user,
        )
        existing.add(key)
        pasted += 1

    messages.success(request, f'Pasted {_entries(pasted)} from {_month_label(clip["year"], clip["month"])}.')
    if dropped_days:
        days = ', '.join(str(d) for d in sorted(set(dropped_days)))
        messages.warning(
            request,
            f'{_entries(len(dropped_days))} dropped because {_month_label(year, month)} has no day {days}.',
        )
    if not_approved:
        messages.warning(request, f'{_entries(not_approved)} skipped because the item is no longer approved for this calendar.')
    if already_there:
        messages.warning(request, f'{_entries(already_there)} skipped because already in this month.')
    return back


def _change_items(request, asg):
    """Supervisor edits of this calendar's approved items (each item sits in the food or non-food column)."""
    post = request.POST
    if 'remove_item' in post:
        ASGApprovedItem.objects.filter(asg=asg, pk=post['remove_item']).delete()
        messages.success(request, 'Item removed from this calendar.')
        return
    item = Enrichment.objects.filter(pk=post.get('item')).first()
    if item is None:
        messages.warning(request, 'Choose an item to add.')
        return
    _, created = ASGApprovedItem.objects.get_or_create(
        asg=asg, item=item, is_food=post['add_item'] == 'food',
        defaults={'comments': post.get('comments', '').strip()[:500], 'rate': post.get('rate', '').strip()[:100]},
    )
    if created:
        messages.success(request, f'Added {item.name}.')
    else:
        messages.warning(request, f'{item.name} is already in that column.')


def _change_concerns_or_goals(request, asg):
    """Supervisor edits of this calendar's special concerns / behavior goals (removing only unlinks them here)."""
    post = request.POST
    if 'remove_concern' in post:
        asg.special_concerns.remove(*SpecialConcern.objects.filter(pk=post['remove_concern']))
        messages.success(request, 'Special concern removed from this calendar.')
    elif 'remove_goal' in post:
        asg.behavior_goals.remove(*BehaviorGoal.objects.filter(pk=post['remove_goal']))
        messages.success(request, 'Behavior goal removed from this calendar.')
    elif 'add_concern' in post:
        text = re.sub(r'\s+', ' ', post['add_concern']).strip()
        if not text or len(text) > 500:
            messages.warning(request, 'Enter a special concern of up to 500 characters.')
            return
        concern = SpecialConcern.objects.filter(text__iexact=text).first() or SpecialConcern.objects.create(text=text)
        asg.special_concerns.add(concern)
        messages.success(request, 'Special concern added.')
    else:
        name = re.sub(r'\s+', ' ', post['add_goal_text']).strip()
        if not name or len(name) > 255:
            messages.warning(request, 'Enter a behavior goal of up to 255 characters.')
            return
        goal = BehaviorGoal.objects.filter(name__iexact=name).first() or BehaviorGoal.objects.create(name=name)
        asg.behavior_goals.add(goal)
        messages.success(request, 'Behavior goal added.')


@supervisor_required
def list_management_tab(request, asg_id):
    asg = _get_accessible_asg(request, asg_id)

    animal_form = AddAnimalChoiceForm(asg=asg)

    if request.method == 'POST':
        if 'remove_animal' in request.POST:
            Animal.objects.filter(asg=asg, pk=request.POST['remove_animal']).delete()
            messages.success(request, 'Animal choice removed.')
            return redirect('zoo:list_management_tab', asg_id=asg.id)
        if 'name' in request.POST:
            animal_form = AddAnimalChoiceForm(request.POST, asg=asg)
            if animal_form.is_valid():
                animal_form.save()
                messages.success(request, 'Animal choice added.')
                return redirect('zoo:list_management_tab', asg_id=asg.id)
        elif any(key in request.POST for key in ('add_concern', 'add_goal_text', 'remove_concern', 'remove_goal')):
            _change_concerns_or_goals(request, asg)
            return redirect('zoo:list_management_tab', asg_id=asg.id)
        elif 'add_item' in request.POST or 'remove_item' in request.POST:
            _change_items(request, asg)
            return redirect('zoo:list_management_tab', asg_id=asg.id)

    assignments = ASGApprovedItem.objects.filter(asg=asg).select_related('item')
    food_items = assignments.filter(is_food=True)
    non_food_items = assignments.filter(is_food=False)

    return render(request, 'zoo/list_management_tab.html', {
        'asg': asg,
        'animal_form': animal_form,
        'concern_suggestions': SpecialConcern.objects.exclude(asgs=asg),
        'goal_suggestions': BehaviorGoal.objects.exclude(asgs=asg),
        'columns': [
            ('Approved non-food enrichment', 'nonfood', Enrichment.objects.exclude(asg_assignments__in=non_food_items), non_food_items),
            ('Approved food enrichment', 'food', Enrichment.objects.exclude(asg_assignments__in=food_items), food_items),
        ],
    })


@login_required
def reporting_view(request, asg_id):
    asg = _get_accessible_asg(request, asg_id)
    entries = CalendarEntry.objects.filter(asg=asg).select_related('item', 'animal', 'behavior_goal').order_by('-date', '-id')
    paginator = Paginator(entries, 50)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'zoo/reporting.html', {'asg': asg, 'page_obj': page_obj})


@login_required
def training_start(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    form = TrainingStringForm(user=request.user, initial={'string': profile.last_training_string_id})
    return render(request, 'zoo/training_start.html', {'form': form, 'can_manage': is_supervisor(request.user)})


@login_required
def training_ajax_animals_for_string(request):
    string_id = request.GET.get('string_id')
    string = String.objects.filter(pk=string_id).first() if string_id else None
    if string is None or not user_can_access_string(request.user, string):
        animals = TrainingAnimal.objects.none()
    else:
        animals = TrainingAnimal.objects.filter(string=string)
    return render(request, 'zoo/animal_options.html', {'animals': animals})


@login_required
def training_history(request, animal_id):
    animal = _get_accessible_training_animal(request, animal_id)
    sessions = animal.training_sessions.select_related('trainer', 'reinforcer_1', 'reinforcer_2', 'reinforcer_3').prefetch_related(
        'behavior_scores__behavior',
    )
    page_obj = Paginator(sessions, 50).get_page(request.GET.get('page'))
    return render(request, 'zoo/training_history.html', {'animal': animal, 'page_obj': page_obj})


@login_required
def training_entry(request, animal_id):
    animal = _get_accessible_training_animal(request, animal_id)
    profile, _ = Profile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = TrainingSessionForm(request.POST, animal=animal)
        if form.is_valid():
            session = TrainingSession.objects.create(
                animal=animal,
                trainer=request.user,
                date=form.cleaned_data['date'],
                session_length_minutes=form.cleaned_data['session_length_minutes'],
                overall_rating=form.cleaned_data['overall_rating'] or None,
                aggression_level=form.cleaned_data['aggression_level'] or None,
                appetite_level=form.cleaned_data['appetite_level'] or None,
                reinforcer_1=form.cleaned_data['reinforcer_1'],
                reinforcer_2=form.cleaned_data['reinforcer_2'],
                reinforcer_3=form.cleaned_data['reinforcer_3'],
                comments=form.cleaned_data['comments'],
            )
            for behavior_id, score in form.behavior_scores().items():
                BehaviorScore.objects.create(session=session, behavior_id=behavior_id, score=score)

            profile.last_training_string = animal.string
            profile.save()

            messages.success(request, f'Training session for {animal} saved.')
            return redirect('zoo:training_start')
    else:
        form = TrainingSessionForm(animal=animal, initial={'date': date.today()})

    return render(request, 'zoo/training_entry.html', {'animal': animal, 'form': form})


@supervisor_required
def item_assignment_view(request):
    if request.method == 'POST':
        form = ItemAssignmentForm(request.POST, divisions=division_scope(request))
        if form.is_valid():
            created = 0
            for item in form.cleaned_data['items']:
                for asg in form.cleaned_data['asgs']:
                    _, was_created = ASGApprovedItem.objects.get_or_create(asg=asg, item=item, is_food=default_is_food(item))
                    created += int(was_created)
            messages.success(request, f'Created {created} new item/calendar assignment(s).')
            return redirect('zoo:item_assignment')
    else:
        form = ItemAssignmentForm(divisions=division_scope(request))

    return render(request, 'zoo/item_assignment.html', {'form': form})


@supervisor_required
def item_ajax_asgs_for_item(request):
    item_id = request.GET.get('item_id')
    asgs = ASG.objects.filter(item_assignments__item_id=item_id) if item_id else ASG.objects.none()
    scope = division_scope(request)
    if scope is not None:
        asgs = asgs.filter(string__division__in=scope)
    return JsonResponse({'asgs': [asg.name for asg in asgs]})


# ---- Manage training logs (supervisors and superusers) ----

def _clean(text):
    return re.sub(r'\s+', ' ', text or '').strip()


def _manageable_strings(request):
    """Strings in the divisions ticked in the title bar (superusers with all ticked: every string)."""
    scope = division_scope(request)
    return String.objects.all() if scope is None else String.objects.filter(division__in=scope)


def _my_divisions(user):
    return available_divisions(user)


def _animal_for(strings, animal_id):
    return get_object_or_404(TrainingAnimal, pk=animal_id, string__in=strings)


def _add_string(request, strings):
    name = _clean(request.POST.get('new_string'))
    divisions = _my_divisions(request.user)
    division = divisions.filter(pk=request.POST.get('new_string_division') or None).first()
    if division is None and not request.user.is_superuser:
        working = division_scope(request)
        division = working.first() if working.count() == 1 else None
        if division is None:
            messages.warning(request, 'Choose one of your divisions for the new string.')
            return
    if not name:
        messages.warning(request, 'Enter a name for the new string.')
    elif String.objects.filter(name__iexact=name).exists():
        messages.warning(request, f'A string named "{name}" already exists.')
    else:
        String.objects.create(name=name, division=division)
        messages.success(request, f'Added string {name}.')


def _rename_string(request, strings, string_id):
    string = get_object_or_404(strings, pk=string_id)
    name = _clean(request.POST.get(f'rename_{string.id}'))
    if not name:
        messages.warning(request, 'A string needs a name.')
    elif String.objects.filter(name__iexact=name).exclude(pk=string.pk).exists():
        messages.warning(request, f'A string named "{name}" already exists.')
    else:
        string.name = name
        string.save()
        messages.success(request, 'String renamed.')


def _set_division(request, strings, string_id):
    if not request.user.is_superuser:
        raise PermissionDenied('Only superusers can change a string\'s division.')
    string = get_object_or_404(strings, pk=string_id)
    string.division = Division.objects.filter(pk=request.POST.get(f'division_{string.id}') or None).first()
    string.save()
    messages.success(request, f'{string.name} is now in {string.division or "no division"}.')


def _delete_string(request, strings, string_id):
    string = get_object_or_404(strings, pk=string_id)
    if string.training_animals.exists() or string.asgs.exists():
        messages.warning(request, f'{string.name} still has training animals or calendars; move or remove them first.')
    else:
        string.delete()
        messages.success(request, f'Deleted string {string.name}.')


def _add_keeper(request, strings, string_id):
    string = get_object_or_404(strings, pk=string_id)
    user = User.objects.filter(pk=request.POST.get(f'new_keeper_{string.id}') or None, is_superuser=False).first()
    if user is None:
        messages.warning(request, 'Choose a user to add.')
    else:
        string.keepers.add(user)
        messages.success(request, f'{user.username.capitalize()} can now use {string.name}.')


def _remove_keeper(request, strings, string_id, user_id):
    string = get_object_or_404(strings, pk=string_id)
    string.keepers.remove(*User.objects.filter(pk=user_id))
    messages.success(request, 'Keeper removed.')


def _add_animal(request, strings, string_id):
    string = get_object_or_404(strings, pk=string_id)
    name = _clean(request.POST.get(f'new_animal_{string.id}'))
    if not name:
        messages.warning(request, 'Enter a name for the animal.')
    elif TrainingAnimal.objects.filter(name__iexact=name).exists():
        messages.warning(request, f'A training animal named "{name}" already exists.')
    else:
        TrainingAnimal.objects.create(name=name, string=string)
        messages.success(request, f'Added {name} to {string.name}.')


def _delete_animal(request, strings, animal_id):
    animal = _animal_for(strings, animal_id)
    animal.delete()
    messages.success(request, f'Deleted {animal.name} and its training sessions.')


def _behavior_manager(animal, kind):
    return animal.maintenance_behaviors if kind == 'maintenance' else animal.new_behaviors


def _add_behavior(request, strings, animal_id, kind):
    animal = _animal_for(strings, animal_id)
    name = _clean(request.POST.get(f'new_behavior_{animal.id}_{kind}'))
    if kind not in ('maintenance', 'new') or not name:
        messages.warning(request, 'Enter a behavior.')
        return
    behavior = Behavior.objects.filter(behavior_type=kind, name__iexact=name).first() \
        or Behavior.objects.create(behavior_type=kind, name=name)
    _behavior_manager(animal, kind).add(behavior)
    messages.success(request, f'Added {behavior.name} to {animal.name}.')


def _remove_behavior(request, strings, animal_id, kind, behavior_id):
    animal = _animal_for(strings, animal_id)
    if kind in ('maintenance', 'new'):
        _behavior_manager(animal, kind).remove(*Behavior.objects.filter(pk=behavior_id))
        messages.success(request, 'Behavior removed.')


def _move_behavior(request, strings, animal_id, behavior_id):
    """New -> Maintenance for this animal (past scores stay on the New behavior they were logged against)."""
    animal = _animal_for(strings, animal_id)
    behavior = get_object_or_404(animal.new_behaviors, pk=behavior_id)
    maintenance = Behavior.objects.filter(behavior_type='maintenance', name__iexact=behavior.name).first() \
        or Behavior.objects.create(behavior_type='maintenance', name=behavior.name)
    animal.new_behaviors.remove(behavior)
    animal.maintenance_behaviors.add(maintenance)
    messages.success(request, f'Moved {behavior.name} to maintenance behaviors for {animal.name}.')


def _add_reinforcer(request, strings, animal_id):
    animal = _animal_for(strings, animal_id)
    name = _clean(request.POST.get(f'new_reinforcer_{animal.id}'))
    if not name:
        messages.warning(request, 'Enter a reinforcer.')
        return
    reinforcer = Reinforcer.objects.filter(name__iexact=name).first() or Reinforcer.objects.create(name=name)
    animal.reinforcers.add(reinforcer)
    messages.success(request, f'Added {reinforcer.name} to {animal.name}.')


def _remove_reinforcer(request, strings, animal_id, reinforcer_id):
    animal = _animal_for(strings, animal_id)
    animal.reinforcers.remove(*Reinforcer.objects.filter(pk=reinforcer_id))
    messages.success(request, 'Reinforcer removed.')


MANAGE_ACTIONS = {
    'add_string': _add_string, 'rename_string': _rename_string, 'set_division': _set_division,
    'delete_string': _delete_string, 'add_keeper': _add_keeper, 'remove_keeper': _remove_keeper,
    'add_animal': _add_animal, 'delete_animal': _delete_animal,
    'add_behavior': _add_behavior, 'remove_behavior': _remove_behavior, 'move_behavior': _move_behavior,
    'add_reinforcer': _add_reinforcer, 'remove_reinforcer': _remove_reinforcer,
}


@supervisor_required
def manage_training(request):
    strings = _manageable_strings(request)
    if request.method == 'POST':
        verb, *ids = request.POST.get('do', '').split(':')
        handler = MANAGE_ACTIONS.get(verb)
        if handler is None:
            messages.warning(request, 'Unknown action.')
        else:
            handler(request, strings, *ids)
        return redirect('zoo:manage_training')

    animals = TrainingAnimal.objects.annotate(n_sessions=Count('training_sessions')).prefetch_related(
        'maintenance_behaviors', 'new_behaviors', 'reinforcers',
    )
    strings = strings.select_related('division').prefetch_related(
        'keepers', Prefetch('training_animals', queryset=animals),
    )
    return render(request, 'zoo/manage_training.html', {
        'strings': strings,
        'divisions': _my_divisions(request.user),
        'is_superuser': request.user.is_superuser,
        'users': User.objects.filter(is_active=True, is_superuser=False).order_by('username'),
        'maintenance_names': Behavior.objects.filter(behavior_type='maintenance').values_list('name', flat=True),
        'new_names': Behavior.objects.filter(behavior_type='new').values_list('name', flat=True),
        'reinforcer_names': Reinforcer.objects.values_list('name', flat=True),
    })


@login_required
@require_POST
def set_divisions(request):
    """Remember which divisions the user ticked in the title bar."""
    chosen = available_divisions(request.user).filter(pk__in=request.POST.getlist('division'))
    if chosen.exists():
        request.session['working_divisions'] = list(chosen.values_list('id', flat=True))
    else:
        messages.warning(request, 'Keep at least one division ticked.')
    next_url = request.POST.get('next', '')
    if not url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        next_url = reverse('zoo:asg_list')
    return redirect(next_url)
