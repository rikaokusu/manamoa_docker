from django import template

register = template.Library()

@register.filter
def is_exist(list, field_name):

    field_number = field_name[6:]

    result = field_number in list

    return result