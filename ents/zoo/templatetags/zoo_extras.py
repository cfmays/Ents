from django import template

from zoo.permissions import is_supervisor as _is_supervisor

register = template.Library()


@register.filter
def is_supervisor(user):
    return _is_supervisor(user)
