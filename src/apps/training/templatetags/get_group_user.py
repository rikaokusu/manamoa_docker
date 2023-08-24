from django import template
from training.models import UserCustomGroupRelation
from accounts.models import User
register = template.Library()

@register.filter
def get_group_user(value):
    print("------------ value", value)#37c58a6f-1f91-499d-9993-447fbb2a81e3

    user_groups = UserCustomGroupRelation.objects.filter(group_id=value)
    print("-------------- groups グループ編集2222", user_groups)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (4)>, <UserCustomGroupRelation: UserCustomGroupRelation object (5)>]>

    group_user_list =[]

    for user_group in user_groups:
        user = User.objects.filter(id=user_group.group_user).first()
        # print("------------ user", user)
        group_user_list.append(user)

    return group_user_list

    # if len(group_user_list) >= 5:
    #     print("------------ メンバーが5人以上います")
    #     return group_user_list[:6]

    # else:
    #     return group_user_list