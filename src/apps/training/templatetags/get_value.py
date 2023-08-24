from django import template
register = template.Library()

@register.filter
def get_value(value):
    print("ばりゅー", value)
    return int(value)
