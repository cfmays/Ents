from django.conf import settings
from django.db import models

from ents.models import Enrichment

SCALE_1_5 = [(i, str(i)) for i in range(1, 6)]

DO_CHOICES = [
    (0, '0 - No Response'),
    (1, '1 - Low Response'),
    (2, '2 - Medium Response'),
    (3, '3 - High Response'),
]

IO_CHOICES = [
    (0, '0 - No Evidence of Response'),
    (1, '1 - Low Evidence of Response'),
    (2, '2 - Medium Evidence of Response'),
    (3, '3 - High Evidence of Response'),
]

GBS_CHOICES = [
    ('G', 'G - Goal behavior achieved'),
    ('A', 'A - Appropriate response, but not goal behavior'),
    ('I', 'I - Inappropriate response'),
    ('N', 'N - No response'),
    ('U', 'U - Unable to evaluate'),
]

BEHAVIOR_TYPE_CHOICES = [
    ('maintenance', 'Maintenance Behavior'),
    ('new', 'New Behavior'),
]


class Division(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class String(models.Model):
    name = models.CharField(max_length=255, unique=True)
    keepers = models.ManyToManyField(settings.AUTH_USER_MODEL, blank=True, related_name='strings')
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True, related_name='strings')

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Profile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    initials = models.CharField(max_length=4, blank=True)
    last_training_string = models.ForeignKey(String, on_delete=models.SET_NULL, null=True, blank=True)
    divisions = models.ManyToManyField(Division, blank=True, related_name='supervisors')

    def __str__(self):
        return f"{self.user} ({self.initials})"


class ItemCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'item categories'

    def __str__(self):
        return self.name


class SpecialConcern(models.Model):
    text = models.CharField(max_length=500, unique=True)

    class Meta:
        ordering = ['text']

    def __str__(self):
        return self.text


class BehaviorGoal(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Behavior(models.Model):
    name = models.CharField(max_length=255)
    behavior_type = models.CharField(max_length=20, choices=BEHAVIOR_TYPE_CHOICES)

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'behavior_type')

    def __str__(self):
        return f"{self.name} ({self.get_behavior_type_display()})"


class Reinforcer(models.Model):
    name = models.CharField(max_length=255, unique=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ASG(models.Model):
    """One calendar tab (e.g. "Tiger"). Its Animal choices live in `animals`."""
    name = models.CharField(max_length=255, unique=True)
    string = models.ForeignKey(String, on_delete=models.PROTECT, related_name='asgs')
    notes = models.TextField(blank=True)
    special_concerns = models.ManyToManyField(SpecialConcern, blank=True, related_name='asgs')
    behavior_goals = models.ManyToManyField(BehaviorGoal, blank=True, related_name='asgs')
    approved_items = models.ManyToManyField(Enrichment, blank=True, through='ASGApprovedItem', related_name='asgs')

    class Meta:
        ordering = ['name']
        verbose_name = 'calendar'
        verbose_name_plural = 'calendars'

    def __str__(self):
        return self.name


class Animal(models.Model):
    """An entry in a calendar's Animal dropdown, e.g. "Rocky" or "Rocky/ Raza/ Nety"."""
    asg = models.ForeignKey(ASG, on_delete=models.CASCADE, related_name='animals', verbose_name='calendar')
    name = models.CharField(max_length=255)

    class Meta:
        ordering = ['name']
        unique_together = ('asg', 'name')
        verbose_name = 'animal choice'
        verbose_name_plural = 'animal choices'

    def __str__(self):
        return self.name


class TrainingAnimal(models.Model):
    """An individual animal in the Training Log."""
    name = models.CharField(max_length=255, unique=True)
    string = models.ForeignKey(String, on_delete=models.PROTECT, related_name='training_animals')
    notes = models.TextField(blank=True)
    maintenance_behaviors = models.ManyToManyField(
        Behavior, blank=True, related_name='training_animals_maintenance',
        limit_choices_to={'behavior_type': 'maintenance'},
    )
    new_behaviors = models.ManyToManyField(
        Behavior, blank=True, related_name='training_animals_new',
        limit_choices_to={'behavior_type': 'new'},
    )
    reinforcers = models.ManyToManyField(Reinforcer, blank=True, related_name='training_animals')

    class Meta:
        ordering = ['name']
        verbose_name = 'training animal'
        verbose_name_plural = 'training animals'

    def __str__(self):
        return self.name


def default_is_food(item):
    """Which column a newly assigned item goes in: food if its category is 'Food'."""
    return item.category is not None and item.category.name == 'Food'


class ASGApprovedItem(models.Model):
    asg = models.ForeignKey(ASG, on_delete=models.CASCADE, related_name='item_assignments', verbose_name='calendar')
    item = models.ForeignKey(Enrichment, on_delete=models.CASCADE, related_name='asg_assignments')
    is_food = models.BooleanField(default=False)  # which column of the calendar's list it sits in
    comments = models.CharField(max_length=500, blank=True)
    rate = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['asg', 'item']
        unique_together = ('asg', 'item', 'is_food')
        verbose_name = 'approved item'
        verbose_name_plural = 'approved items'

    def __str__(self):
        return f"{self.item} → {self.asg}"


class CalendarEntry(models.Model):
    asg = models.ForeignKey(ASG, on_delete=models.CASCADE, related_name='calendar_entries', verbose_name='calendar')
    animal = models.ForeignKey(Animal, on_delete=models.SET_NULL, null=True, blank=True, related_name='calendar_entries')
    date = models.DateField()
    item = models.ForeignKey(Enrichment, on_delete=models.PROTECT, related_name='calendar_entries')
    behavior_goal = models.ForeignKey(BehaviorGoal, on_delete=models.SET_NULL, null=True, blank=True)
    do_score = models.IntegerField(choices=DO_CHOICES, null=True, blank=True)
    io_score = models.IntegerField(choices=IO_CHOICES, null=True, blank=True)
    gbs_score = models.CharField(max_length=1, choices=GBS_CHOICES, blank=True)
    notes = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['date', 'id']
        verbose_name_plural = 'calendar entries'

    def __str__(self):
        return f"{self.asg} {self.date} {self.item}"


class TrainingSession(models.Model):
    animal = models.ForeignKey(TrainingAnimal, on_delete=models.CASCADE, related_name='training_sessions')
    trainer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='training_sessions')
    date = models.DateField()
    session_length_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    overall_rating = models.IntegerField(choices=SCALE_1_5, null=True, blank=True)
    aggression_level = models.IntegerField(choices=SCALE_1_5, null=True, blank=True)
    appetite_level = models.IntegerField(choices=SCALE_1_5, null=True, blank=True)
    # ordered attempts: the keeper starts with reinforcer_1 and only fills in the next
    # slot if that one didn't work, so these are separate fields rather than a set.
    reinforcer_1 = models.ForeignKey(Reinforcer, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reinforcer_2 = models.ForeignKey(Reinforcer, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    reinforcer_3 = models.ForeignKey(Reinforcer, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    comments = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f"{self.animal} {self.date} ({self.trainer})"

    def reinforcers(self):
        """The reinforcers tried, in order."""
        return [r for r in (self.reinforcer_1, self.reinforcer_2, self.reinforcer_3) if r]


class BehaviorScore(models.Model):
    session = models.ForeignKey(TrainingSession, on_delete=models.CASCADE, related_name='behavior_scores')
    behavior = models.ForeignKey(Behavior, on_delete=models.CASCADE)
    score = models.IntegerField(choices=SCALE_1_5)

    class Meta:
        ordering = ['behavior']
        unique_together = ('session', 'behavior')

    def __str__(self):
        return f"{self.behavior}: {self.score}"
