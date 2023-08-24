from django import template
from accounts.models import User
from training.models import CoAdminUserManagement, CoAdminUserManagementRelation
register = template.Library()

@register.filter
def get_co_admin_user(value):
    print("---------------value", value.id)# 28caa177-ce84-411f-9775-bffc81d22075

    # ログインしているユーザーが共同管理者か調べる
    # co_admin_user_objects = CoAdminUserManagement.objects.filter(co_admin_user__in=[value])
    co_admin_user_objects = CoAdminUserManagementRelation.objects.filter(co_admin_user_id__in=[value.id])
    print("---------------co_admin_user_objects", co_admin_user_objects)

    return co_admin_user_objects
