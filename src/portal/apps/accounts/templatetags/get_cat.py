from django import template

register = template.Library()

@register.filter
def get_cat(List, key):

    name_values = [x['category'] for x in List if x['id'] == key]

    category = name_values[0] if len(name_values) else ''

    return category