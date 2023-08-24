from django import template
from accounts.models import User

register = template.Library()

@register.filter
def set_order(queryset, value):
    obj = queryset.all().order_by(value)
    if obj:
        return obj

