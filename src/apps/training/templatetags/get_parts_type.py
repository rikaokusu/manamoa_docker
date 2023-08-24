from django import template
from training.models import Parts

register = template.Library()

@register.filter
def get_parts_type(queryset, value):
    obj = queryset.filter(type=value)

    if obj:
        return obj

