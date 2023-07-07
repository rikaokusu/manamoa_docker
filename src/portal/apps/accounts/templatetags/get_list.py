from django import template

register = template.Library()

@register.filter
def get_list(List, key):

    name_values = [x['price'] for x in List if x['id'] == key]

    price = name_values[0] if len(name_values) else ''

    return price