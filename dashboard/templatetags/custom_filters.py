from django import template

register = template.Library()

@register.filter
def get_member(members, user):
    """
    Returns the member object from a queryset/list of members
    that matches the given user, or None if not found.
    """
    return next((m for m in members if m.user_account == user), None)
