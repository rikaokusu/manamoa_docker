from django import template
register = template.Library()

@register.filter
def zfill(value, int):
    return str(value).zfill(int)
