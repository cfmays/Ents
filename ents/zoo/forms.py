from django import forms
from django.forms import modelformset_factory

from ents.forms import EnrichmentSelect
from ents.models import Enrichment

from .models import ASG, Animal, BehaviorGoal, CalendarEntry, Reinforcer, SCALE_1_5, String


def item_labels_for(asg):
    """{item id: "Item name **comment"}, like the sheet's combined list, so keepers see the notes when choosing."""
    comments = {}
    for assignment in asg.item_assignments.select_related('item'):
        label_comments = comments.setdefault(assignment.item_id, (assignment.item.name, []))[1]
        if assignment.comments and assignment.comments not in label_comments:
            label_comments.append(assignment.comments)
    return {
        item_id: f"{name} **{' | '.join(notes)}" if notes else name
        for item_id, (name, notes) in comments.items()
    }


def make_calendar_entry_form(asg):
    """Build a CalendarEntry ModelForm whose choice fields are scoped to one calendar."""

    labels = item_labels_for(asg)

    class CalendarEntryForm(forms.ModelForm):
        class Meta:
            model = CalendarEntry
            fields = ['date', 'animal', 'item', 'behavior_goal', 'do_score', 'io_score', 'gbs_score', 'notes']
            widgets = {
                'date': forms.DateInput(attrs={'type': 'date'}),
                'item': EnrichmentSelect(attrs={'class': 'item-select'}),
                'notes': forms.TextInput(),
                'do_score': forms.Select(attrs={'class': 'score-select'}),
                'io_score': forms.Select(attrs={'class': 'score-select'}),
                'gbs_score': forms.Select(attrs={'class': 'score-select'}),
            }

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.fields['animal'].queryset = asg.animals.all()
            self.fields['animal'].required = False
            self.fields['item'].queryset = Enrichment.objects.filter(asgs=asg).distinct()
            self.fields['item'].label_from_instance = lambda item: labels.get(item.id, item.name)
            self.fields['behavior_goal'].queryset = asg.behavior_goals.all()
            self.fields['behavior_goal'].required = False
            self.fields['date'].required = False
            self.fields['item'].required = False

        def clean(self):
            cleaned = super().clean()
            # blank rows are skipped by Django; a row with anything filled in needs a date and an item
            if self.has_changed():
                if not cleaned.get('date'):
                    self.add_error('date', 'Please enter a date.')
                if not cleaned.get('item'):
                    self.add_error('item', 'Please choose an enrichment item.')
            return cleaned

    return CalendarEntryForm


def make_calendar_entry_formset(asg, extra=5):
    form_class = make_calendar_entry_form(asg)
    FormSet = modelformset_factory(CalendarEntry, form=form_class, extra=extra, can_delete=False)
    return FormSet


class AddBehaviorGoalForm(forms.Form):
    behavior_goal = forms.ModelChoiceField(queryset=BehaviorGoal.objects.all(), label='Add a behavior goal')

    def __init__(self, *args, asg=None, **kwargs):
        super().__init__(*args, **kwargs)
        if asg is not None:
            self.fields['behavior_goal'].queryset = BehaviorGoal.objects.exclude(asgs=asg)


class AddAnimalChoiceForm(forms.ModelForm):
    class Meta:
        model = Animal
        fields = ['name']
        labels = {'name': 'Add an animal choice (e.g. Rocky/ Raza)'}

    def __init__(self, *args, asg, **kwargs):
        super().__init__(*args, **kwargs)
        self.instance.asg = asg


class TrainingStringForm(forms.Form):
    string = forms.ModelChoiceField(queryset=String.objects.all(), label='String')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None:
            self.fields['string'].queryset = user.strings.all()


class TrainingSessionForm(forms.Form):
    date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    session_length_minutes = forms.IntegerField(required=False, min_value=1, label='Session length (minutes)')
    overall_rating = forms.TypedChoiceField(choices=[('', '—')] + SCALE_1_5, coerce=int, required=False,
                                             label='Overall session rating (1 = Refused, 5 = Perfect)')
    aggression_level = forms.TypedChoiceField(choices=[('', '—')] + SCALE_1_5, coerce=int, required=False,
                                               label='Aggression level (1 = Low, 5 = High)')
    appetite_level = forms.TypedChoiceField(choices=[('', '—')] + SCALE_1_5, coerce=int, required=False,
                                             label='Appetite level (1 = Low, 5 = High)')
    reinforcer_1 = forms.ModelChoiceField(queryset=Reinforcer.objects.none(), required=False, label='Reinforcers 1')
    reinforcer_2 = forms.ModelChoiceField(queryset=Reinforcer.objects.none(), required=False, label='Reinforcers 2')
    reinforcer_3 = forms.ModelChoiceField(queryset=Reinforcer.objects.none(), required=False, label='Reinforcers 3')
    comments = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))

    def __init__(self, *args, animal, **kwargs):
        super().__init__(*args, **kwargs)
        self.animal = animal
        self.fields['reinforcer_1'].queryset = animal.reinforcers.all()
        self.fields['reinforcer_2'].queryset = animal.reinforcers.all()
        self.fields['reinforcer_3'].queryset = animal.reinforcers.all()

        self.maintenance_fields = []
        for behavior in animal.maintenance_behaviors.all():
            field_name = f'behavior_{behavior.id}'
            self.fields[field_name] = forms.TypedChoiceField(
                choices=[('', '—')] + SCALE_1_5, coerce=int, required=False, label=behavior.name,
            )
            self.maintenance_fields.append(field_name)

        self.new_behavior_fields = []
        for behavior in animal.new_behaviors.all():
            field_name = f'behavior_{behavior.id}'
            self.fields[field_name] = forms.TypedChoiceField(
                choices=[('', '—')] + SCALE_1_5, coerce=int, required=False, label=behavior.name,
            )
            self.new_behavior_fields.append(field_name)

    def maintenance_bound_fields(self):
        return [self[name] for name in self.maintenance_fields]

    def new_behavior_bound_fields(self):
        return [self[name] for name in self.new_behavior_fields]

    def behavior_scores(self):
        """Return {behavior_id: score} for every behavior field the keeper actually scored."""
        scores = {}
        for name, value in self.cleaned_data.items():
            if name.startswith('behavior_') and value not in (None, ''):
                behavior_id = int(name.split('_', 1)[1])
                scores[behavior_id] = value
        return scores


class ItemAssignmentForm(forms.Form):
    items = forms.ModelMultipleChoiceField(queryset=Enrichment.objects.all(), widget=forms.SelectMultiple(attrs={'size': 10}))
    asgs = forms.ModelMultipleChoiceField(queryset=ASG.objects.all(), widget=forms.SelectMultiple(attrs={'size': 10}), label='Calendars')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_superuser:
            self.fields['asgs'].queryset = ASG.objects.filter(string__division__in=user.profile.divisions.all())
