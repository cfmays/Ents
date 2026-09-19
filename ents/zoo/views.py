import calendar
from datetime import date

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from .forms import AddAnimalChoiceForm, AddBehaviorGoalForm, ItemAssignmentForm, TrainingSessionForm, TrainingStringForm, make_calendar_entry_formset
from .models import ASG, ASGApprovedItem, Animal, default_is_food, BehaviorScore, CalendarEntry, Profile, String, TrainingAnimal, TrainingSession
from .permissions import supervisor_required, user_can_access_asg, user_can_access_string, user_can_access_training_animal


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
    if request.user.is_superuser:
        strings = String.objects.all()
    else:
        profile = getattr(request.user, 'profile', None)
        divisions = profile.divisions.all() if profile else []
        strings = String.objects.filter(Q(keepers=request.user) | Q(division__in=divisions)).distinct()
    strings = strings.prefetch_related('asgs')
    return render(request, 'zoo/asg_list.html', {'strings': strings})


@login_required
def calendar_tab(request, asg_id, year=None, month=None):
    asg = _get_accessible_asg(request, asg_id)
    today = date.today()
    year = int(year) if year else today.year
    month = int(month) if month else today.month

    days_in_month = calendar.monthrange(year, month)[1]
    month_start = date(year, month, 1)
    month_end = date(year, month, days_in_month)

    FormSet = make_calendar_entry_formset(asg, year, month)
    queryset = CalendarEntry.objects.filter(asg=asg, date__gte=month_start, date__lte=month_end)

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
            return redirect('zoo:calendar_tab', asg_id=asg.id, year=year, month=month)
    else:
        formset = FormSet(queryset=queryset)

    prev_month = (month_start.replace(day=1) - date.resolution).replace(day=1)
    next_month = (month_end + date.resolution)

    clip = request.session.get('calendar_clipboard')
    clipboard = None
    if clip and clip['asg_id'] == asg.id:
        clipboard = f"{_entries(len(clip['entries']))} from {_month_label(clip['year'], clip['month'])}"

    return render(request, 'zoo/calendar_tab.html', {
        'asg': asg,
        'clipboard': clipboard,
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


@login_required
def list_management_tab(request, asg_id):
    asg = _get_accessible_asg(request, asg_id)

    form = AddBehaviorGoalForm(asg=asg)
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
        else:
            form = AddBehaviorGoalForm(request.POST, asg=asg)
            if form.is_valid():
                asg.behavior_goals.add(form.cleaned_data['behavior_goal'])
                messages.success(request, 'Behavior goal added.')
                return redirect('zoo:list_management_tab', asg_id=asg.id)

    assignments = ASGApprovedItem.objects.filter(asg=asg).select_related('item')
    food_items = assignments.filter(is_food=True)
    non_food_items = assignments.filter(is_food=False)

    return render(request, 'zoo/list_management_tab.html', {
        'asg': asg,
        'form': form,
        'animal_form': animal_form,
        'food_items': food_items,
        'non_food_items': non_food_items,
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
    return render(request, 'zoo/training_start.html', {'form': form})


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
        form = ItemAssignmentForm(request.POST, user=request.user)
        if form.is_valid():
            created = 0
            for item in form.cleaned_data['items']:
                for asg in form.cleaned_data['asgs']:
                    _, was_created = ASGApprovedItem.objects.get_or_create(asg=asg, item=item, is_food=default_is_food(item))
                    created += int(was_created)
            messages.success(request, f'Created {created} new item/calendar assignment(s).')
            return redirect('zoo:item_assignment')
    else:
        form = ItemAssignmentForm(user=request.user)

    return render(request, 'zoo/item_assignment.html', {'form': form})


@supervisor_required
def item_ajax_asgs_for_item(request):
    item_id = request.GET.get('item_id')
    asgs = ASG.objects.filter(item_assignments__item_id=item_id) if item_id else ASG.objects.none()
    if not request.user.is_superuser:
        asgs = asgs.filter(string__division__in=request.user.profile.divisions.all())
    return JsonResponse({'asgs': [asg.name for asg in asgs]})
