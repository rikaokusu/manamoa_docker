from django import template

register = template.Library()

@register.filter
def get_file_id_value(queryset, value):
    movie_play_manage = queryset.filter(file_id=value).first()
    if movie_play_manage:
        return movie_play_manage.status.id
    else:
        return 1

