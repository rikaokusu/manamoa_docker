from django import template
register = template.Library()

@register.filter
def subtraction(value, arg):
    #arg = list(map(int, arg))
    result = int(value) - int(arg)
    # {{ 1|subtraction:10 }} = 9
    return result