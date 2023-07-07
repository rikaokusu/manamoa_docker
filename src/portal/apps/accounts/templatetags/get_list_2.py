from django import template

register = template.Library()

@register.filter
def get_list_2(queryset, cat):
    if cat:
        option = queryset.filter(category=cat).first()
        if option:
            return option.price
        else:
            return 0
    else:

        return None