from django import template

register = template.Library()

@register.filter()
def is_exists(queryset, value):
    if queryset:
        return queryset.filter(file_id=value).exists()
    else:
        pass