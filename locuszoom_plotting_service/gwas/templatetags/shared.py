from django import template
import furl

register = template.Library()

@register.filter(name='add_token')
def add_token(value, token):
    """Generate an absolute URL that includes a private link token as a query param"""
    if not token:
        return value
    return furl.furl(value).add({'token': token}).url
