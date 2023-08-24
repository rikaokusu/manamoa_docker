from django import template
register = template.Library()

@register.filter
def get_list(value):
    print("bbbbbbbbbbbbbbbbb", value)

    # value = -value
    # value =- value
    print("aaaaaaaaaaaaaaa", value)

    return list(range(value))