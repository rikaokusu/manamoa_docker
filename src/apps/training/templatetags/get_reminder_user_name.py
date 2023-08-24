from django import template
from training.models import UserCustomGroupRelation
from accounts.models import User
register = template.Library()

@register.filter
def get_reminder_user_name(value):
    print("------------ value", value)#37c58a6f-1f91-499d-9993-447fbb2a81e3

    user = User.objects.filter(id=value).first()
    print("-------------- ユーザー名", user.display_name)# <QuerySet [<UserCustomGroupRelation: UserCustomGroupRelation object (4)>, <UserCustomGroupRelation: UserCustomGroupRelation object (5)>]>

    display_name = user.display_name

    return display_name