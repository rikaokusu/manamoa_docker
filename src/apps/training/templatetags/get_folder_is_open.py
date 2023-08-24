from django import template

register = template.Library()

@register.filter
def get_folder_is_open(queryset, obj):
    folder_is_open = queryset.filter(training=obj).first()

    if folder_is_open is None:
        return True
    else:
        return folder_is_open.is_open

