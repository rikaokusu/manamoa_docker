from django import template
register = template.Library()

@register.filter
def append(value,arg):
    for i in range(arg):
        value.append(None)
    return value