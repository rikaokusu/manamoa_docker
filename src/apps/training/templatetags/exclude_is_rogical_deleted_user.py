from django import template
from accounts.models import User
from training.models import CustomGroup

register = template.Library()

@register.filter
def exclude_is_rogical_deleted_user(queryset):
    # 論理削除済みのユーザーは除外して返す
    obj = queryset.all().exclude(is_rogical_deleted=True)

    return obj