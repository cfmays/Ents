from django.contrib import admin

from .models import (
    ASG,
    ASGApprovedItem,
    Animal,
    Behavior,
    BehaviorGoal,
    BehaviorScore,
    CalendarEntry,
    Division,
    ItemCategory,
    Profile,
    Reinforcer,
    SpecialConcern,
    String,
    TrainingAnimal,
    TrainingSession,
)
from .permissions import is_supervisor


class DivisionScopedAdminMixin:
    """Restricts a Supervisor's queryset/choices to their assigned Division(s).

    Superusers see everything, as always. `division_lookup` is the field path from
    this admin's model to Division; `division_scoped_fk_fields` maps an FK field
    name on this model to *its own* path to Division, so the "add" form's dropdown
    for that FK only offers in-scope choices.
    """

    division_lookup = None
    division_scoped_fk_fields = {}

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if not is_supervisor(request.user):
            return qs.none()
        profile = getattr(request.user, 'profile', None)
        divisions = profile.divisions.all() if profile else Division.objects.none()
        return qs.filter(**{f'{self.division_lookup}__in': divisions})

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        lookup = self.division_scoped_fk_fields.get(db_field.name)
        if lookup and not request.user.is_superuser and is_supervisor(request.user):
            profile = getattr(request.user, 'profile', None)
            divisions = profile.divisions.all() if profile else Division.objects.none()
            kwargs['queryset'] = db_field.related_model.objects.filter(**{f'{lookup}__in': divisions})
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Division)
class DivisionAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(SpecialConcern)
class SpecialConcernAdmin(admin.ModelAdmin):
    search_fields = ['text']


@admin.register(BehaviorGoal)
class BehaviorGoalAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(Behavior)
class BehaviorAdmin(admin.ModelAdmin):
    list_display = ['name', 'behavior_type']
    list_filter = ['behavior_type']
    search_fields = ['name']


@admin.register(Reinforcer)
class ReinforcerAdmin(admin.ModelAdmin):
    search_fields = ['name']


@admin.register(String)
class StringAdmin(DivisionScopedAdminMixin, admin.ModelAdmin):
    division_lookup = 'division'
    list_display = ['name', 'division']
    list_filter = ['division']
    filter_horizontal = ['keepers']
    search_fields = ['name']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'initials', 'last_training_string']
    list_editable = ['initials']
    autocomplete_fields = ['last_training_string']
    filter_horizontal = ['divisions']
    search_fields = ['user__username', 'initials']


class AnimalInline(admin.TabularInline):
    model = Animal
    extra = 1


class ASGApprovedItemInline(admin.TabularInline):
    model = ASGApprovedItem
    extra = 1
    autocomplete_fields = ['item']


@admin.register(ASG)
class ASGAdmin(DivisionScopedAdminMixin, admin.ModelAdmin):
    division_lookup = 'string__division'
    division_scoped_fk_fields = {'string': 'division'}
    list_display = ['name', 'string']
    list_filter = ['string']
    search_fields = ['name']
    filter_horizontal = ['special_concerns', 'behavior_goals']
    inlines = [AnimalInline, ASGApprovedItemInline]


@admin.register(Animal)
class AnimalAdmin(DivisionScopedAdminMixin, admin.ModelAdmin):
    division_lookup = 'asg__string__division'
    division_scoped_fk_fields = {'asg': 'string__division'}
    list_display = ['name', 'asg']
    list_filter = ['asg']
    search_fields = ['name']


@admin.register(TrainingAnimal)
class TrainingAnimalAdmin(DivisionScopedAdminMixin, admin.ModelAdmin):
    division_lookup = 'string__division'
    division_scoped_fk_fields = {'string': 'division'}
    list_display = ['name', 'string']
    list_filter = ['string']
    search_fields = ['name']
    filter_horizontal = ['maintenance_behaviors', 'new_behaviors', 'reinforcers']


@admin.register(CalendarEntry)
class CalendarEntryAdmin(DivisionScopedAdminMixin, admin.ModelAdmin):
    division_lookup = 'asg__string__division'
    division_scoped_fk_fields = {'asg': 'string__division'}
    list_display = ['asg', 'animal', 'date', 'item', 'gbs_score', 'created_by']
    list_filter = ['asg', 'date']
    date_hierarchy = 'date'
    autocomplete_fields = ['item']


class BehaviorScoreInline(admin.TabularInline):
    model = BehaviorScore
    extra = 0


@admin.register(TrainingSession)
class TrainingSessionAdmin(DivisionScopedAdminMixin, admin.ModelAdmin):
    division_lookup = 'animal__string__division'
    division_scoped_fk_fields = {'animal': 'string__division'}
    list_display = ['animal', 'date', 'trainer', 'overall_rating']
    list_filter = ['animal', 'date']
    date_hierarchy = 'date'
    inlines = [BehaviorScoreInline]
