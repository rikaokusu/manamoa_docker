from django import template
from accounts.models import User

register = template.Library()

@register.filter
def get_model_obj(queryset, value):
    # print("------ queryset", queryset)#  <QuerySet []>
    # print("------ value get_model_obj", value)# テストユーザー / user@user.com
    # print("------ id get_model_obj", value.id)# 28caa177-ce84-411f-9775-bffc81d22075

    user = User.objects.filter(id=value.id).first()
    # print("------ user", user.id)# テストユーザー / user@user.com

    # obj = queryset.filter(user=user).first()
    obj = queryset.filter(user=user.id).first()
    # print("------ obj", obj)

    if obj:
        return obj

