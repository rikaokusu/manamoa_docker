from django import template
from training.models import UserCustomGroupRelation
from accounts.models import User, Company
register = template.Library()

@register.filter
def get_reminder_user_company_pic_dept_name(value):
    # print("------------ value", value)#37c58a6f-1f91-499d-9993-447fbb2a81e3

    user = User.objects.filter(id=value).first()
    # print("-------------- user", user)
    # print("-------------- ユーザー名", user.display_name)
    # print("-------------- 会社名", user.company.pic_company_name)
    # print("-------------- 所属", user.company.pic_dept_name)

    # company_pic_dept_name = user.company.pic_company_name
    company_pic_dept_name = user.company.pic_dept_name

    return company_pic_dept_name