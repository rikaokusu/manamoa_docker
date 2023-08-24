from django import template
register = template.Library()

@register.filter
def get_int(value):

    return int(value)