from django import template
register = template.Library()

@register.filter
def total_list(list):
    # リストの全要素数をカウント: len()
    return len(list)