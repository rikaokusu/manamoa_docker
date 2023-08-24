from django import template
register = template.Library()

@register.filter
def count_list(list, arg):
    # Trueがlistに何個含まれているかを調べる=リスト.count(値)
    return list.count("True")