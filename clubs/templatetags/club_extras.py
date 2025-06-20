# clubs/templatetags/club_extras.py

from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Return the value from a dictionary for a given key."""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None
