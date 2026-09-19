from django import forms
from django.contrib import admin, messages

from ents.models import Enrichment
from zoo.models import ASG, ASGApprovedItem, default_is_food


class AssignToASGsForm(forms.Form):
    asgs = forms.ModelMultipleChoiceField(queryset=ASG.objects.all(), widget=forms.CheckboxSelectMultiple, label='Calendars')

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user is not None and not user.is_superuser:
            self.fields['asgs'].queryset = ASG.objects.filter(string__division__in=user.profile.divisions.all())


@admin.register(Enrichment)
class EnrichmentAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'is_food']
    list_filter = ['category', 'is_food']
    search_fields = ['name']
    actions = ['assign_to_asgs']

    @admin.action(description='Assign selected items to calendar(s)')
    def assign_to_asgs(self, request, queryset):
        if 'apply' in request.POST:
            form = AssignToASGsForm(request.POST, user=request.user)
            if form.is_valid():
                asgs = form.cleaned_data['asgs']
                created = 0
                for item in queryset:
                    for asg in asgs:
                        _, was_created = ASGApprovedItem.objects.get_or_create(asg=asg, item=item, is_food=default_is_food(item))
                        created += int(was_created)
                self.message_user(
                    request,
                    f"Created {created} new item/calendar assignment(s).",
                    messages.SUCCESS,
                )
                return None
        else:
            form = AssignToASGsForm(user=request.user)

        from django.shortcuts import render
        return render(request, 'admin/assign_to_asgs.html', {
            'items': queryset,
            'form': form,
            'action_checkbox_name': admin.helpers.ACTION_CHECKBOX_NAME,
        })
