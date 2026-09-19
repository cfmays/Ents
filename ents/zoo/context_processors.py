from .permissions import available_divisions, picked_divisions


def division_picker(request):
    """Checkbox data for the title bar: only for people who can work in more than one division."""
    if not request.user.is_authenticated:
        return {}
    available = available_divisions(request.user)
    if available.count() < 2:
        return {}
    picked = set(picked_divisions(request).values_list('id', flat=True))
    return {'division_picker': [(division, division.id in picked) for division in available]}
