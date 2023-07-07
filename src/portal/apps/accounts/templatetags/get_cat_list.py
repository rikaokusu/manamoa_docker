from django import template

register = template.Library()

@register.filter
def get_cat_list(List, key):

    number = key - 1

    if number < 0:
        return List[0]

    else:
        return List[number]