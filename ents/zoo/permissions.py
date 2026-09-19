from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .models import Division


def is_supervisor(user):
    return user.is_authenticated and (user.is_superuser or user.groups.filter(name='Supervisor').exists())


def supervisor_required(view_func):
    @login_required
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not is_supervisor(request.user):
            raise PermissionDenied("This page is for supervisors only.")
        return view_func(request, *args, **kwargs)
    return wrapper


def user_can_access_string(user, string):
    """True if `user` may view/edit a String's calendars/training animals.

    Keepers only get Strings they're actually assigned to; supervisors get
    anything in a Division they're assigned to (matching the admin scoping);
    superusers get everything.
    """
    if user.is_superuser:
        return True
    if string.keepers.filter(pk=user.pk).exists():
        return True
    if is_supervisor(user):
        profile = getattr(user, 'profile', None)
        if profile and string.division_id and profile.divisions.filter(pk=string.division_id).exists():
            return True
    return False


def user_can_access_asg(user, asg):
    return user_can_access_string(user, asg.string)


def user_can_access_training_animal(user, animal):
    return user_can_access_string(user, animal.string)


def available_divisions(user):
    """Divisions a user can work in: all for superusers, their profile's for supervisors, none for keepers."""
    if user.is_superuser:
        return Division.objects.all()
    profile = getattr(user, 'profile', None)
    return profile.divisions.all() if profile and is_supervisor(user) else Division.objects.none()


def picked_divisions(request):
    """The divisions ticked in the title bar (all available ones until the user picks)."""
    available = available_divisions(request.user)
    chosen = request.session.get('working_divisions')
    if chosen:
        picked = available.filter(pk__in=chosen)
        if picked.exists():
            return picked
    return available


def division_scope(request):
    """Divisions to filter by, or None for "no filter" (a superuser with every division ticked)."""
    picked = picked_divisions(request)
    if request.user.is_superuser and picked.count() == available_divisions(request.user).count():
        return None
    return picked
