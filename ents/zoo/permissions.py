from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied


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
