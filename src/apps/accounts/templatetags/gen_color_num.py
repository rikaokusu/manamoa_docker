from django import template
register = template.Library()

@register.filter
def gen_color_num(value):
    num_row = str(value)[-1]
    num = num_row.zfill(2)
    return num
