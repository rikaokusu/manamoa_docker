from django import template
register = template.Library()

@register.filter
def gen_index(value, arg):
    return value + arg
